"""Video Models"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field


class VideoStatus(str, Enum):
    """Video download status"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class VideoBase(BaseModel):
    """Base video model"""
    title: str
    show: str
    url: str
    thumbnail_url: str = ""
    season: Optional[str] = None
    episode: Optional[str] = None
    year: Optional[int] = None
    duration: int = 0
    duration_str: str = ""
    hls_url: Optional[str] = None


class VideoCreate(VideoBase):
    """Video creation model"""
    id: str


class VideoUpdate(BaseModel):
    """Video update model"""
    title: Optional[str] = None
    hls_url: Optional[str] = None
    status: Optional[VideoStatus] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    progress: Optional[float] = None
    error_message: Optional[str] = None


class Video(VideoBase):
    """Full video model"""
    id: str
    status: VideoStatus = VideoStatus.PENDING
    file_path: Optional[str] = None
    file_size: int = 0
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class VideoResponse(BaseModel):
    """Video list response"""
    total: int
    videos: List[Video]
    page: int = 1
    page_size: int = 50


class VideoStats(BaseModel):
    """Video statistics"""
    total: int
    pending: int
    downloading: int
    completed: int
    failed: int
    total_size: int  # bytes
    shows: List[str]
    years: List[int]
