from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

    # Encrypted API configurations
    ocr_api_base = Column(String, nullable=True)
    ocr_api_key = Column(String, nullable=True)  # Encrypted
    ocr_model = Column(String, nullable=True)

    translate_api_base = Column(String, nullable=True)
    translate_api_key = Column(String, nullable=True)  # Encrypted
    translate_model = Column(String, nullable=True)

    embedding_api_base = Column(String, nullable=True)
    embedding_api_key = Column(String, nullable=True)  # Encrypted
    embedding_model = Column(String, nullable=True)
    embedding_dimension = Column(Integer, nullable=True, default=768)  # Vector dimension
