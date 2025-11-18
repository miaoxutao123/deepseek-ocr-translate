import os
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # App
    APP_NAME: str = "OCR and Translate System"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200

    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./ocr_translate.db"

    # File Upload
    MAX_FILE_SIZE_MB: int = 1024
    UPLOAD_DIR: str = "./uploads"

    # OCR Settings
    OCR_PAGE_THRESHOLD: int = 1
    OCR_MAX_RETRIES: int = 3
    OCR_RETRY_DELAYS: str = "2,4,8"

    # Poppler path (for PDF processing on Windows)
    # If not set, pdf2image will try to find poppler in PATH
    # Example: C:\Program Files\poppler\Library\bin
    POPPLER_PATH: Optional[str] = None

    # Translation Settings
    CORRECTION_TOKEN_THRESHOLD: int = 4000
    VECTOR_SIMILARITY_THRESHOLD: float = 0.85

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def retry_delays(self) -> List[int]:
        return [int(x) for x in self.OCR_RETRY_DELAYS.split(",")]

    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
