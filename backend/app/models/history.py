from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
import enum
from ..database import Base


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(str, enum.Enum):
    OCR = "ocr"
    TRANSLATE = "translate"
    OCR_TRANSLATE = "ocr_translate"


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_type = Column(SQLEnum(TaskType), nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)

    # File information
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)

    # Progress tracking
    current_page = Column(Integer, nullable=True, default=0)
    total_pages = Column(Integer, nullable=True, default=0)
    progress_message = Column(String, nullable=True)

    # OCR results (JSON string with page info)
    ocr_result = Column(Text, nullable=True)

    # Translation results (JSON string with sentence pairs)
    translation_result = Column(Text, nullable=True)

    # Language info
    source_language = Column(String, nullable=True)
    target_language = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error information
    error_message = Column(Text, nullable=True)
