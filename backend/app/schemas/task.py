from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from ..models.history import TaskType, TaskStatus


class OCRRequest(BaseModel):
    """Request for OCR operation"""
    # File will be uploaded separately
    source_language: Optional[str] = "auto"
    page_threshold: Optional[int] = 1


class OCRPageResult(BaseModel):
    """Result for a single page OCR"""
    page_number: int
    text: str
    confidence: Optional[float] = None


class OCRResponse(BaseModel):
    """Response for OCR operation"""
    task_id: int
    pages: List[OCRPageResult]
    total_pages: int


class TranslationRequest(BaseModel):
    """Request for translation operation"""
    source_language: str = Field(..., description="Source language code (en, de, ru, zh)")
    target_language: str = Field(default="zh", description="Target language code")
    # Either provide text directly or history_id to translate OCR results
    text: Optional[str] = None
    history_id: Optional[int] = None


class SentencePair(BaseModel):
    """A pair of source and translated sentences"""
    source: str
    translation: str
    page_numbers: Optional[List[int]] = None


class TranslationResponse(BaseModel):
    """Response for translation operation"""
    task_id: int
    sentences: List[SentencePair]
    total_sentences: int


class TaskStatusResponse(BaseModel):
    """Response for task status"""
    task_id: int
    status: TaskStatus
    message: Optional[str] = None


class HistoryResponse(BaseModel):
    """Response for history entry"""
    id: int
    task_type: TaskType
    status: TaskStatus
    original_filename: str
    source_language: Optional[str]
    target_language: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    ocr_result: Optional[str] = None
    translation_result: Optional[str] = None

    # Progress tracking
    current_page: Optional[int] = None
    total_pages: Optional[int] = None
    progress_message: Optional[str] = None

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v else None  # 添加 Z 表示 UTC 时间
        }


class HistoryListResponse(BaseModel):
    """Response for history list"""
    items: List[HistoryResponse]
    total: int
    page: int
    page_size: int
