"""Video Data Model"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class VideoStatus(Enum):
    """Video download status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class Video:
    """Video data model"""
    id: str
    title: str
    show: str
    url: str
    thumbnail_url: str = ""
    season: Optional[str] = None
    episode: Optional[str] = None
    year: Optional[int] = None
    duration: int = 0  # seconds
    duration_str: str = ""
    hls_url: Optional[str] = None
    status: VideoStatus = VideoStatus.PENDING
    file_path: Optional[str] = None
    file_size: int = 0  # bytes
    progress: float = 0.0  # 0-100
    speed: float = 0.0  # bytes/s
    eta: int = 0  # seconds
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    @property
    def file_size_str(self) -> str:
        """Human readable file size"""
        if self.file_size >= 1024 * 1024 * 1024:
            return f"{self.file_size / (1024**3):.2f} GB"
        elif self.file_size >= 1024 * 1024:
            return f"{self.file_size / (1024**2):.1f} MB"
        elif self.file_size >= 1024:
            return f"{self.file_size / 1024:.0f} KB"
        return f"{self.file_size} B"

    @property
    def speed_str(self) -> str:
        """Human readable speed"""
        if self.speed >= 1024 * 1024:
            return f"{self.speed / (1024**2):.1f} MB/s"
        elif self.speed >= 1024:
            return f"{self.speed / 1024:.0f} KB/s"
        return f"{self.speed:.0f} B/s"

    @property
    def eta_str(self) -> str:
        """Human readable ETA"""
        if self.eta <= 0:
            return "--:--"
        hours, remainder = divmod(self.eta, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{int(hours)}:{int(minutes):02d}:{int(seconds):02d}"
        return f"{int(minutes)}:{int(seconds):02d}"

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "show": self.show,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "season": self.season,
            "episode": self.episode,
            "year": self.year,
            "duration": self.duration,
            "duration_str": self.duration_str,
            "hls_url": self.hls_url,
            "status": self.status.value,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "progress": self.progress,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Video":
        """Create from dictionary"""
        return cls(
            id=data["id"],
            title=data["title"],
            show=data.get("show", "Unknown"),
            url=data["url"],
            thumbnail_url=data.get("thumbnail_url", ""),
            season=data.get("season"),
            episode=data.get("episode"),
            year=data.get("year"),
            duration=data.get("duration", 0),
            duration_str=data.get("duration_str", ""),
            hls_url=data.get("hls_url"),
            status=VideoStatus(data.get("status", "pending")),
            file_path=data.get("file_path"),
            file_size=data.get("file_size", 0),
            progress=data.get("progress", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
        )
