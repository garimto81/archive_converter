"""Application Configuration"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # App
    app_name: str = "PokerGO Downloader"
    app_version: str = "2.0.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Database - shared with app
    database_path: Path = Path(__file__).parent.parent.parent.parent / "data" / "pokergo" / "pokergo.db"

    # Download
    download_path: Path = Path("downloads")
    default_quality: str = "Best"
    max_concurrent_downloads: int = 2

    # PokerGO Credentials
    pokergo_email: Optional[str] = None
    pokergo_password: Optional[str] = None

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"
        env_prefix = "POKERGO_"


settings = Settings()
