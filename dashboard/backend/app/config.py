"""
Application configuration using Pydantic Settings.
"""
from pydantic import field_validator
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

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # NAS 설정
    nas_mount_path: str = "Z:\\ARCHIVE"  # Windows: Z:\ARCHIVE, Linux: /mnt/nas
    nas_use_real_data: bool = True  # True: 실제 NAS, False: Mock 데이터

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
