"""Download Models"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class DownloadStatus(str, Enum):
    """Download queue status"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadRequest(BaseModel):
    """Download request"""
    video_ids: List[str]
    quality: str = "Best"


class DownloadProgress(BaseModel):
    """Download progress update (WebSocket)"""
    video_id: str
    progress: float  # 0-100
    speed: float  # bytes/s
    eta: int  # seconds
    status: DownloadStatus


class DownloadQueueItem(BaseModel):
    """Download queue item"""
    id: int
    video_id: str
    video_title: str
    priority: int = 0
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: float = 0.0
    eta: int = 0
    error_message: Optional[str] = None


class DownloadQueueResponse(BaseModel):
    """Download queue response"""
    active: List[DownloadQueueItem]
    queued: List[DownloadQueueItem]
    completed: List[DownloadQueueItem]
    total_active: int
    total_queued: int
