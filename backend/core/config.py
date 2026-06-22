"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_NAME: str = "RupeeRadar"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:80"]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    MAX_UPLOAD_SIZE_BYTES: int = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    ALLOWED_EXTENSIONS: list[str] = [".csv", ".pdf"]
    UPLOAD_DIR: str = "uploads"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./rupeeradar.db"

    # AI / LLM (used in Phase 2+)
    LLM_PROVIDER: Literal["groq", "openai", "local"] = "groq"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_CATEGORIZATION_BATCH_SIZE: int = 15
    AI_CONFIDENCE_THRESHOLD: float = 0.9
    AI_TIMEOUT_SECONDS: int = 30

    # Job Processing
    JOB_TIMEOUT_SECONDS: int = 300  # 5 minutes
    JOB_CLEANUP_TTL_SECONDS: int = 3600  # 1 hour
    JOB_POLL_INTERVAL_SECONDS: int = 2

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent

    # Look for .env in the backend/ directory (where this config file lives)
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

# Ensure upload directory exists
os.makedirs(os.path.join(settings.BASE_DIR, settings.UPLOAD_DIR), exist_ok=True)
