from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


class APIConfig(BaseModel):
    """API configuration for OCR, Translation, and Embedding"""
    ocr_api_base: Optional[str] = None
    ocr_api_key: Optional[str] = None
    ocr_model: Optional[str] = "deepseek-ai/deepseek-vl2"

    translate_api_base: Optional[str] = None
    translate_api_key: Optional[str] = None
    translate_model: Optional[str] = None

    embedding_api_base: Optional[str] = "https://generativelanguage.googleapis.com/v1beta"
    embedding_api_key: Optional[str] = None
    embedding_model: Optional[str] = "text-embedding-004"
    embedding_dimension: Optional[int] = 768


class APIConfigResponse(BaseModel):
    """Response model that shows config without sensitive keys"""
    ocr_api_base: Optional[str] = None
    ocr_model: Optional[str] = None
    ocr_api_key_set: bool = False

    translate_api_base: Optional[str] = None
    translate_model: Optional[str] = None
    translate_api_key_set: bool = False

    embedding_api_base: Optional[str] = None
    embedding_model: Optional[str] = None
    embedding_dimension: Optional[int] = None
    embedding_api_key_set: bool = False
