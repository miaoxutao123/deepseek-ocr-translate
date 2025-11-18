from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from ..database import get_db
from ..models import User
from ..schemas import (
    CorrectionCreate,
    CorrectionResponse,
    CorrectionListResponse,
    CorrectionImportRequest,
    CorrectionExportResponse,
)
from ..services import CorrectionService
from .auth import get_current_user

router = APIRouter(prefix="/corrections", tags=["corrections"])


@router.post("", response_model=CorrectionResponse)
async def create_correction(
    correction_data: CorrectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new correction entry"""
    correction_service = CorrectionService(db, current_user)
    correction = await correction_service.create_correction(correction_data)
    return correction


@router.get("", response_model=CorrectionListResponse)
def get_corrections(
    source_language: str = None,
    target_language: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's corrections with optional filtering"""
    from ..models import Correction

    query = db.query(Correction).filter(Correction.user_id == current_user.id)

    if source_language:
        query = query.filter(Correction.source_language == source_language)
    if target_language:
        query = query.filter(Correction.target_language == target_language)

    total = query.count()
    corrections = query.order_by(Correction.created_at.desc()).offset(offset).limit(limit).all()

    return CorrectionListResponse(items=corrections, total=total)


@router.delete("/{correction_id}")
def delete_correction(
    correction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a correction"""
    correction_service = CorrectionService(db, current_user)
    success = correction_service.delete_correction(correction_id)

    if not success:
        raise HTTPException(status_code=404, detail="Correction not found")

    return {"message": "Correction deleted successfully"}


@router.post("/import")
async def import_corrections(
    import_data: CorrectionImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import corrections from backup"""
    correction_service = CorrectionService(db, current_user)
    count = await correction_service.import_corrections(import_data.corrections)

    return {
        "message": f"Successfully imported {count} corrections",
        "imported_count": count
    }


@router.get("/export", response_model=CorrectionExportResponse)
def export_corrections(
    source_language: str = None,
    target_language: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export corrections for backup"""
    correction_service = CorrectionService(db, current_user)
    corrections = correction_service.export_corrections(source_language, target_language)

    return CorrectionExportResponse(
        corrections=corrections,
        exported_at=datetime.utcnow(),
        total_count=len(corrections)
    )
