import json
import os
import re
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path

from ..database import get_db
from ..models import User, History
from ..schemas import HistoryResponse, HistoryListResponse
from ..services import ExportService
from ..config import settings
from .auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
def get_history(
    page: int = 1,
    page_size: int = 20,
    task_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's translation history"""
    query = db.query(History).filter(History.user_id == current_user.id)

    if task_type:
        query = query.filter(History.task_type == task_type)

    total = query.count()

    histories = query.order_by(History.created_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return HistoryListResponse(
        items=histories,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{history_id}", response_model=HistoryResponse)
def get_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed history entry"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    return history


@router.delete("/{history_id}")
def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a history entry"""
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    # Delete associated file if exists
    if history.file_path and os.path.exists(history.file_path):
        try:
            os.remove(history.file_path)
        except Exception:
            pass

    db.delete(history)
    db.commit()

    return {"message": "History deleted successfully"}


@router.get("/{history_id}/export")
async def export_translation(
    history_id: int,
    format: str = "markdown",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export translation results to various formats"""
    # Validate format
    supported_formats = ["markdown", "txt", "docx", "pdf"]
    if format not in supported_formats:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format. Supported: {', '.join(supported_formats)}"
        )

    # Get history
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if not history.translation_result:
        raise HTTPException(status_code=400, detail="No translation result available")

    # Parse translation results
    translation_data = json.loads(history.translation_result)

    # Prepare output path
    export_dir = Path(settings.UPLOAD_DIR) / str(current_user.id) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    base_filename = Path(history.original_filename).stem
    output_filename = f"{base_filename}_translation.{format}"
    output_path = export_dir / output_filename

    # Language names
    language_names = {
        "en": "English",
        "zh": "Chinese",
        "de": "German",
        "ru": "Russian"
    }
    source_lang = language_names.get(history.source_language, history.source_language)
    target_lang = language_names.get(history.target_language, history.target_language)

    # Export to file
    ExportService.export_translation(
        translation_data,
        str(output_path),
        format,
        source_lang,
        target_lang
    )

    # Return file
    return FileResponse(
        path=str(output_path),
        filename=output_filename,
        media_type="application/octet-stream"
    )


def clean_deepseek_tags(text: str) -> tuple:
    """
    清理文本中的 DeepSeek-OCR 标签

    Returns:
        (清理后的文本, 清理的字符数)
    """
    if not text:
        return text, 0

    original_length = len(text)

    # Remove complete tag pairs: <|ref|>...<|/ref|><|det|>...<|/det|>
    text = re.sub(r'<\|ref\|>.*?<\/\|ref\|><\|det\|>.*?<\/\|det\|>\s*', '', text)

    # Remove standalone coordinate arrays like: text[[x, y, w, h]]
    text = re.sub(r'\[\[\d+,\s*\d+,\s*\d+,\s*\d+\]\]', '', text)

    # Remove any remaining special tokens like <|grounding|>, <|ref|>, <|/ref|>, etc.
    text = re.sub(r'<\|[^|]+\|>', '', text)

    # Remove content type labels (title, sub_title, text, image, etc.)
    # Pattern: word at start of line followed by newline
    text = re.sub(r'^(title|sub_title|text|image|caption|header|footer|table|figure)\s*\n', '', text, flags=re.MULTILINE)

    # Clean up multiple consecutive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    cleaned_length = len(text)
    removed_chars = original_length - cleaned_length

    return text, removed_chars


@router.post("/{history_id}/clean-tags")
def clean_ocr_tags(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean DeepSeek-OCR tags from a specific history entry"""
    # Get history
    history = db.query(History).filter(
        History.id == history_id,
        History.user_id == current_user.id
    ).first()

    if not history:
        raise HTTPException(status_code=404, detail="History not found")

    if not history.ocr_result:
        raise HTTPException(status_code=400, detail="No OCR result available")

    # Parse OCR result
    try:
        ocr_data = json.loads(history.ocr_result)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid OCR result format")

    # Clean each page
    total_removed = 0
    for page in ocr_data:
        if 'text' in page:
            cleaned_text, removed = clean_deepseek_tags(page['text'])
            page['text'] = cleaned_text
            total_removed += removed

    # Update database
    history.ocr_result = json.dumps(ocr_data, ensure_ascii=False)
    db.commit()

    logger.info(f"Cleaned {total_removed} characters from history {history_id}")

    return {
        "message": "Tags cleaned successfully",
        "removed_chars": total_removed
    }


@router.post("/clean-all-tags")
def clean_all_ocr_tags(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clean DeepSeek-OCR tags from all user's history entries"""
    # Get all histories with OCR results
    histories = db.query(History).filter(
        History.user_id == current_user.id,
        History.ocr_result.isnot(None),
        History.ocr_result != ""
    ).all()

    total_records = 0
    total_removed = 0

    for history in histories:
        try:
            ocr_data = json.loads(history.ocr_result)

            # Clean each page
            needs_update = False
            record_removed = 0

            for page in ocr_data:
                if 'text' in page:
                    cleaned_text, removed = clean_deepseek_tags(page['text'])
                    if removed > 0:
                        page['text'] = cleaned_text
                        needs_update = True
                        record_removed += removed

            # Update database
            if needs_update:
                history.ocr_result = json.dumps(ocr_data, ensure_ascii=False)
                total_records += 1
                total_removed += record_removed

        except json.JSONDecodeError:
            logger.error(f"Failed to parse OCR result for history {history.id}")
            continue

    # Commit all changes
    db.commit()

    logger.info(f"Cleaned {total_records} records, removed {total_removed} characters total")

    return {
        "message": "All tags cleaned successfully",
        "cleaned_records": total_records,
        "total_removed_chars": total_removed
    }
