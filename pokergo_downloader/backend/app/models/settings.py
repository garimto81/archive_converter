"""Settings Models"""

from typing import Optional
from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    """Settings update request"""
    pokergo_email: Optional[str] = None
    pokergo_password: Optional[str] = None
    download_path: Optional[str] = None
    video_quality: Optional[str] = None
    max_concurrent_downloads: Optional[int] = None
    auto_fetch_hls: Optional[bool] = None


class SettingsResponse(BaseModel):
    """Settings response"""
    pokergo_email: Optional[str] = None
    download_path: str
    video_quality: str
    max_concurrent_downloads: int
    auto_fetch_hls: bool
    is_logged_in: bool = False


class LoginTestRequest(BaseModel):
    """Login test request"""
    email: str
    password: str


class LoginTestResponse(BaseModel):
    """Login test response"""
    success: bool
    message: str
