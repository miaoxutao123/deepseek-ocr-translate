from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class CorrectionCreate(BaseModel):
    """Create a new correction"""
    source_text: str = Field(..., min_length=1)
    corrected_translation: str = Field(..., min_length=1)
    source_language: str
    target_language: str
    history_id: Optional[int] = None


class CorrectionResponse(BaseModel):
    """Response for correction entry"""
    id: int
    source_text: str
    corrected_translation: str
    source_language: str
    target_language: str
    created_at: datetime
    usage_count: int
    last_used_at: Optional[datetime]

    class Config:
        from_attributes = True


class CorrectionListResponse(BaseModel):
    """Response for correction list"""
    items: List[CorrectionResponse]
    total: int


class CorrectionImportRequest(BaseModel):
    """Request to import corrections"""
    corrections: List[CorrectionCreate]


class CorrectionExportResponse(BaseModel):
    """Response for correction export"""
    corrections: List[CorrectionResponse]
    exported_at: datetime
    total_count: int
