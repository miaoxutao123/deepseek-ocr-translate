#!/usr/bin/env python3
"""
清理 OCR 历史记录中的 DeepSeek-OCR 坐标标签

此脚本会扫描数据库中所有历史记录，清除 OCR 结果中的坐标标签，
例如: text[[236, 255, 741, 325]]

用法:
    python clean_ocr_tags.py              # 预览需要清理的记录
    python clean_ocr_tags.py --apply      # 实际执行清理
    python clean_ocr_tags.py --backup     # 执行清理并备份数据库
"""

import sys
import os
import re
import json
import shutil
from datetime import datetime
from pathlib import Path

# 添加 app 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.history import History, TaskType
from app.config import settings


def clean_deepseek_tags(text: str) -> tuple[str, int]:
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


def backup_database(db_path: str) -> str:
    """备份数据库"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return None


def preview_cleaning(session):
    """预览需要清理的记录"""
    print("\n" + "=" * 60)
    print("预览模式 - 扫描需要清理的记录")
    print("=" * 60 + "\n")

    # 查询所有有 OCR 结果的记录
    histories = session.query(History).filter(
        History.ocr_result.isnot(None),
        History.ocr_result != ""
    ).all()

    total_records = 0
    total_removed = 0
    records_to_clean = []

    for history in histories:
        try:
            ocr_data = json.loads(history.ocr_result)

            # 检查每个页面的文本
            needs_cleaning = False
            total_page_removed = 0

            for page in ocr_data:
                if 'text' in page:
                    cleaned_text, removed = clean_deepseek_tags(page['text'])
                    if removed > 0:
                        needs_cleaning = True
                        total_page_removed += removed

            if needs_cleaning:
                total_records += 1
                total_removed += total_page_removed
                records_to_clean.append({
                    'id': history.id,
                    'filename': history.original_filename,
                    'pages': len(ocr_data),
                    'removed': total_page_removed
                })

        except json.JSONDecodeError:
            continue

    # 显示结果
    if total_records == 0:
        print("✅ 未发现需要清理的记录\n")
        return False

    print(f"📊 发现 {total_records} 条记录需要清理:\n")

    for record in records_to_clean[:10]:  # 只显示前10条
        print(f"  ID: {record['id']:4d} | {record['filename'][:40]:40s} | "
              f"{record['pages']} 页 | 清理 {record['removed']} 字符")

    if len(records_to_clean) > 10:
        print(f"  ... 还有 {len(records_to_clean) - 10} 条记录 ...")

    print(f"\n💡 总计将清理 {total_removed} 个字符的标签")
    print("\n提示: 使用 --apply 参数执行清理, --backup 参数同时备份数据库\n")

    return True


def apply_cleaning(session, backup: bool = False):
    """执行清理"""
    # 备份数据库
    if backup:
        db_path = str(settings.DATABASE_URL).replace('sqlite:///', '')
        if not backup_database(db_path):
            print("❌ 备份失败，取消清理操作")
            return

    print("\n" + "=" * 60)
    print("执行清理 - 处理中...")
    print("=" * 60 + "\n")

    # 查询所有有 OCR 结果的记录
    histories = session.query(History).filter(
        History.ocr_result.isnot(None),
        History.ocr_result != ""
    ).all()

    total_records = 0
    total_removed = 0

    for history in histories:
        try:
            ocr_data = json.loads(history.ocr_result)

            # 清理每个页面的文本
            needs_update = False
            record_removed = 0

            for page in ocr_data:
                if 'text' in page:
                    cleaned_text, removed = clean_deepseek_tags(page['text'])
                    if removed > 0:
                        page['text'] = cleaned_text
                        needs_update = True
                        record_removed += removed

            # 更新数据库
            if needs_update:
                history.ocr_result = json.dumps(ocr_data, ensure_ascii=False)
                total_records += 1
                total_removed += record_removed

                print(f"  ✓ ID {history.id:4d} | {history.original_filename[:40]:40s} | "
                      f"清理了 {record_removed} 字符")

        except json.JSONDecodeError as e:
            print(f"  ✗ ID {history.id:4d} | JSON 解析错误: {e}")
            continue

    # 提交更改
    try:
        session.commit()
        print(f"\n✅ 清理完成!")
        print(f"   - 处理了 {total_records} 条记录")
        print(f"   - 总计清理 {total_removed} 个字符\n")
    except Exception as e:
        session.rollback()
        print(f"\n❌ 提交失败: {e}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='清理 OCR 历史记录中的 DeepSeek-OCR 坐标标签',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python clean_ocr_tags.py              预览需要清理的记录
  python clean_ocr_tags.py --apply      执行清理
  python clean_ocr_tags.py --backup     执行清理并备份数据库
        """
    )

    parser.add_argument('--apply', action='store_true',
                       help='执行清理（默认只预览）')
    parser.add_argument('--backup', action='store_true',
                       help='清理前备份数据库')

    args = parser.parse_args()

    # 创建数据库会话
    db_url = str(settings.DATABASE_URL)
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        if args.apply or args.backup:
            apply_cleaning(session, backup=args.backup)
        else:
            has_records = preview_cleaning(session)
            if not has_records:
                return 0
            return 1
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
