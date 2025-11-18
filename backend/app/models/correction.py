from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from ..database import Base


class Correction(Base):
    __tablename__ = "corrections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Original text and corrected translation
    source_text = Column(Text, nullable=False)
    corrected_translation = Column(Text, nullable=False)

    # Language info
    source_language = Column(String, nullable=False)
    target_language = Column(String, nullable=False)

    # Vector embedding for similarity search (stored as JSON array)
    embedding = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    usage_count = Column(Integer, default=0)  # Track how many times this correction was applied
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Optional: link to history entry where this correction was created
    history_id = Column(Integer, ForeignKey("history.id"), nullable=True)
