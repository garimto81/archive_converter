"""
Application configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # App Info
    app_name: str = "Archive Dashboard Backend"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/api"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:4000",
        "http://localhost:4001",
        "http://localhost:5173",
    ]

    # NAS (for future use)
    nas_mount_path: str = "/mnt/nas"

    # Database (for future use)
    database_url: str = "postgresql://user:pass@db:5432/archive"

    # Redis (for future use)
    redis_url: str = "redis://redis:6379"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
