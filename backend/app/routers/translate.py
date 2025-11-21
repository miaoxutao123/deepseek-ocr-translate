import json
import logging
import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models import User, History, TaskStatus, TaskType
from ..schemas import TranslationRequest, TranslationResponse, SentencePair, TaskStatusResponse
from ..services import TranslationService
from ..config import settings
from ..utils import EncryptionManager
from .auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/translate", tags=["translation"])

# 存储翻译任务的暂停状态（内存中，生产环境可以用 Redis）
translation_task_states = {}


def get_user_translation_service(user: User, db: Session) -> TranslationService:
    """Create translation service for user"""
    if not user.translate_api_key:
        raise HTTPException(status_code=400, detail="Translation API key not configured")

    api_key = EncryptionManager.decrypt_api_key(
        user.translate_api_key, user.id, settings.SECRET_KEY
    )
    api_base = user.translate_api_base or "https://api.openai.com/v1"
    model = user.translate_model or "gpt-4"

    return TranslationService(api_base, api_key, model, db, user)


async def background_translate_task(
    history_id: int,
    sentences: list[str],
    source_language: str,
    target_language: str,
    user_id: int,
    api_base: str,
    api_key: str,
    model: str,
    start_index: int = 0  # 从哪个句子开始
):
    """Background task for translation with progress updates"""
    from ..database import SessionLocal

    db = SessionLocal()
    try:
        # Get history and user
        history = db.query(History).filter(History.id == history_id).first()
        user = db.query(User).filter(User.id == user_id).first()

        if not history or not user:
            logger.error(f"History {history_id} or user {user_id} not found")
            return

        # Update status to processing
        history.status = TaskStatus.PROCESSING
        history.total_pages = len(sentences)  # Use total_pages for total sentences
        history.current_page = start_index
        db.commit()

        # Initialize task state
        translation_task_states[history_id] = {
            "paused": False,
            "stopped": False,
            "sentences": sentences  # 保存句子列表用于继续翻译
        }

        # Create translation service
        translate_service = TranslationService(api_base, api_key, model, db, user)

        # Load existing translated sentences if resuming
        translated_pairs = []
        if start_index > 0 and history.translation_result:
            try:
                translated_pairs = json.loads(history.translation_result)
            except json.JSONDecodeError:
                pass

        # Translate one by one with progress updates
        for index in range(start_index, len(sentences)):
            sentence = sentences[index]

            # Check if paused or stopped
            task_state = translation_task_states.get(history_id, {})

            # 如果暂停，等待继续
            while task_state.get("paused", False):
                history.status = "paused"
                history.progress_message = f"已暂停，当前进度: {index}/{len(sentences)}"
                db.commit()
                await asyncio.sleep(1)
                task_state = translation_task_states.get(history_id, {})

                # 如果被停止，退出
                if task_state.get("stopped", False):
                    break

            # 检查是否停止
            if task_state.get("stopped", False):
                history.status = "stopped"
                history.progress_message = f"翻译已停止，完成 {index}/{len(sentences)} 句"
                db.commit()
                logger.info(f"翻译任务 {history_id} 已停止，完成 {index}/{len(sentences)} 句")
                return

            try:
                logger.info(f"翻译第 {index + 1}/{len(sentences)} 句")

                # Update status back to processing
                history.status = TaskStatus.PROCESSING

                # Update progress
                history.current_page = index + 1
                history.progress_message = f"正在翻译第 {index + 1}/{len(sentences)} 句..."
                db.commit()

                # Translate single sentence
                translation = await translate_service.translate_text(
                    sentence,
                    source_language,
                    target_language,
                    use_corrections=True
                )

                # Add to results
                translated_pairs.append({
                    "source": sentence,
                    "translation": translation
                })

                # Save intermediate results
                history.translation_result = json.dumps(translated_pairs, ensure_ascii=False)
                db.commit()

            except Exception as e:
                logger.error(f"翻译第 {index + 1} 句失败: {str(e)}")
                translated_pairs.append({
                    "source": sentence,
                    "translation": f"[翻译错误: {str(e)}]"
                })
                history.translation_result = json.dumps(translated_pairs, ensure_ascii=False)
                db.commit()

        # Mark as completed
        history.status = TaskStatus.COMPLETED
        history.completed_at = datetime.utcnow()
        history.progress_message = "翻译完成"
        db.commit()

        logger.info(f"✅ 翻译任务 {history_id} 完成，共 {len(sentences)} 句")

    except Exception as e:
        logger.error(f"翻译任务 {history_id} 失败: {str(e)}")
        if history:
            history.status = TaskStatus.FAILED
            history.error_message = str(e)
            db.commit()
    finally:
        # 清理任务状态
        if history_id in translation_task_states:
            del translation_task_states[history_id]
        db.close()


@router.post("/start", response_model=TaskStatusResponse)
async def translate(
    request: TranslationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start translation task (runs in background)

    Either provide 'text' directly or 'history_id' to translate OCR results
    """
    logger.info("=" * 60)
    logger.info("翻译请求开始")
    logger.info("=" * 60)
    logger.info(f"用户: {current_user.username} (ID: {current_user.id})")
    logger.info(f"源语言: {request.source_language}")
    logger.info(f"目标语言: {request.target_language}")
    logger.info(f"请求类型: {'直接文本' if request.text else f'历史记录 ID {request.history_id}'}")

    # Get translation service config
    if not current_user.translate_api_key:
        raise HTTPException(status_code=400, detail="Translation API key not configured")

    api_key = EncryptionManager.decrypt_api_key(
        current_user.translate_api_key, current_user.id, settings.SECRET_KEY
    )
    api_base = current_user.translate_api_base or "https://api.openai.com/v1"
    model = current_user.translate_model or "gpt-4"

    logger.info(f"翻译模型: {model}")
    logger.info(f"API Base: {api_base}")

    # Determine source text and create history
    if request.text:
        source_text = request.text
        logger.info(f"使用直接输入的文本，长度: {len(source_text)} 字符")

        # Create new history entry for translation only
        new_history = History(
            user_id=current_user.id,
            task_type=TaskType.TRANSLATE,
            status=TaskStatus.PENDING,
            original_filename="text_input.txt",
            source_language=request.source_language,
            target_language=request.target_language
        )
        db.add(new_history)
        db.commit()
        db.refresh(new_history)
        history_id = new_history.id

    elif request.history_id:
        # Get OCR results from history
        logger.info(f"从历史记录加载 OCR 结果: {request.history_id}")
        history = db.query(History).filter(
            History.id == request.history_id,
            History.user_id == current_user.id
        ).first()

        if not history:
            logger.error(f"历史记录未找到: {request.history_id}")
            raise HTTPException(status_code=404, detail="History not found")

        if not history.ocr_result:
            logger.error(f"历史记录无 OCR 结果: {request.history_id}")
            raise HTTPException(status_code=400, detail="No OCR result available")

        # Extract text from OCR results and merge cross-page sentences
        ocr_results = json.loads(history.ocr_result)
        logger.info(f"OCR 结果包含 {len(ocr_results)} 页")

        # Merge text from pages, handling cross-page sentences
        merged_text_parts = []
        for i, page in enumerate(ocr_results):
            text = page["text"].strip()
            if not text:
                continue

            # If this is not the first page and previous text doesn't end with sentence ending
            # and current text doesn't start with capital letter, merge them
            if merged_text_parts and not re.search(r'[.!?。！？]\s*$', merged_text_parts[-1]):
                # Check if current text looks like continuation (doesn't start with capital or number)
                if text and not re.match(r'^[A-Z0-9#\[]', text):
                    # Merge with previous (cross-page sentence)
                    merged_text_parts[-1] = merged_text_parts[-1].rstrip() + ' ' + text
                else:
                    # New sentence/paragraph
                    merged_text_parts.append(text)
            else:
                merged_text_parts.append(text)

        source_text = "\n\n".join(merged_text_parts)
        history_id = request.history_id

        # Update history
        history.task_type = TaskType.OCR_TRANSLATE
        history.source_language = request.source_language
        history.target_language = request.target_language
        history.status = TaskStatus.PENDING
        db.commit()

        logger.info(f"提取的文本长度: {len(source_text)} 字符")
    else:
        logger.error("请求中未提供文本或历史记录 ID")
        raise HTTPException(status_code=400, detail="Either 'text' or 'history_id' must be provided")

    # Split text into sentences
    logger.info("-" * 60)
    logger.info("分割文本为句子...")
    sentences = TranslationService.split_and_merge_text(
        source_text, request.source_language
    )
    logger.info(f"分割完成，共 {len(sentences)} 个句子")

    # Start background translation task
    logger.info("启动后台翻译任务...")
    background_tasks.add_task(
        background_translate_task,
        history_id=history_id,
        sentences=sentences,
        source_language=request.source_language,
        target_language=request.target_language,
        user_id=current_user.id,
        api_base=api_base,
        api_key=api_key,
        model=model,
        start_index=0
    )

    logger.info(f"✅ 翻译任务已创建: {history_id}")
    logger.info("=" * 60)

    return TaskStatusResponse(
        task_id=history_id,
        status=TaskStatus.PENDING,
        message="Translation task started"
    )


@router.post("/pause/{history_id}")
def pause_translation(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Pause a running translation task"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if history_id in translation_task_states:
        translation_task_states[history_id]["paused"] = True
        logger.info(f"翻译任务 {history_id} 已暂停")
        return {"message": "Translation paused", "task_id": history_id}
    else:
        raise HTTPException(status_code=400, detail="Translation task not running")


@router.post("/resume/{history_id}")
async def resume_translation(
    history_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resume a paused translation task"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    # 如果任务还在内存中（只是暂停状态），直接恢复
    if history_id in translation_task_states:
        translation_task_states[history_id]["paused"] = False
        logger.info(f"翻译任务 {history_id} 继续")
        return {"message": "Translation resumed", "task_id": history_id}

    # 如果任务不在内存中（可能服务重启了），需要重新启动
    # 从数据库中获取已翻译的进度
    if history.status in ["paused", "stopped", TaskStatus.PROCESSING]:
        # 获取翻译服务配置
        if not current_user.translate_api_key:
            raise HTTPException(status_code=400, detail="Translation API key not configured")

        api_key = EncryptionManager.decrypt_api_key(
            current_user.translate_api_key, current_user.id, settings.SECRET_KEY
        )
        api_base = current_user.translate_api_base or "https://api.openai.com/v1"
        model = current_user.translate_model or "gpt-4"

        # 获取已翻译的句子数
        start_index = history.current_page or 0

        # 需要重新分割文本（或从保存的状态中恢复）
        # 这里简化处理：如果有 OCR 结果，重新提取文本
        if history.ocr_result:
            ocr_results = json.loads(history.ocr_result)
            merged_text_parts = []
            for page in ocr_results:
                text = page["text"].strip()
                if text:
                    merged_text_parts.append(text)
            source_text = "\n\n".join(merged_text_parts)
        else:
            raise HTTPException(status_code=400, detail="Cannot resume: no source text available")

        sentences = TranslationService.split_and_merge_text(
            source_text, history.source_language or "auto"
        )

        # 启动后台任务从上次位置继续
        background_tasks.add_task(
            background_translate_task,
            history_id=history_id,
            sentences=sentences,
            source_language=history.source_language or "auto",
            target_language=history.target_language or "zh",
            user_id=current_user.id,
            api_base=api_base,
            api_key=api_key,
            model=model,
            start_index=start_index
        )

        logger.info(f"翻译任务 {history_id} 从第 {start_index} 句继续")
        return {"message": f"Translation resumed from sentence {start_index}", "task_id": history_id}

    raise HTTPException(status_code=400, detail="Translation task cannot be resumed")


@router.post("/stop/{history_id}")
def stop_translation(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stop a running translation task"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if history_id in translation_task_states:
        translation_task_states[history_id]["stopped"] = True
        translation_task_states[history_id]["paused"] = False  # 取消暂停以允许循环退出
        logger.info(f"翻译任务 {history_id} 已停止")
        return {"message": "Translation stopped", "task_id": history_id}
    else:
        # 任务可能已经完成或不存在
        history.status = "stopped"
        db.commit()
        return {"message": "Translation marked as stopped", "task_id": history_id}


@router.get("/progress/{history_id}")
def get_translation_progress(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time translation progress"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    # Parse current translation results
    translated_pairs = []
    if history.translation_result:
        try:
            translated_pairs = json.loads(history.translation_result)
        except json.JSONDecodeError:
            pass

    return {
        "task_id": history.id,
        "status": history.status,
        "current": history.current_page or 0,
        "total": history.total_pages or 0,
        "message": history.progress_message,
        "translations": translated_pairs,
        "error": history.error_message
    }


@router.get("/result/{history_id}", response_model=TranslationResponse)
def get_translation_result(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get translation results for a history entry"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if not history.translation_result:
        raise HTTPException(status_code=404, detail="Translation result not found")

    translation_data = json.loads(history.translation_result)
    sentence_pairs = [SentencePair(**pair) for pair in translation_data]

    return TranslationResponse(
        task_id=history.id,
        sentences=sentence_pairs,
        total_sentences=len(sentence_pairs)
    )
