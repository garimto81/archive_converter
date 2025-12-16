"""Downloads API Router"""

from typing import List
from fastapi import APIRouter, HTTPException

from ..models.download import (
    DownloadRequest,
    DownloadQueueItem,
    DownloadQueueResponse,
    DownloadStatus,
)
from ..services.download_manager import get_download_manager

router = APIRouter()


@router.get("", response_model=DownloadQueueResponse)
async def get_queue():
    """Get download queue status"""
    manager = get_download_manager()
    return manager.get_queue_status()


@router.post("")
async def add_downloads(request: DownloadRequest):
    """Add videos to download queue"""
    manager = get_download_manager()
    added = manager.add_to_queue(request.video_ids, request.quality)
    return {"added": added, "total_requested": len(request.video_ids)}


@router.delete("/{video_id}")
async def cancel_download(video_id: str):
    """Cancel a download"""
    manager = get_download_manager()
    if manager.cancel_download(video_id):
        return {"message": "Download cancelled"}
    raise HTTPException(status_code=404, detail="Download not found")


@router.patch("/{video_id}/pause")
async def pause_download(video_id: str):
    """Pause a download"""
    manager = get_download_manager()
    if manager.pause_download(video_id):
        return {"message": "Download paused"}
    raise HTTPException(status_code=404, detail="Download not found or not pausable")


@router.patch("/{video_id}/resume")
async def resume_download(video_id: str):
    """Resume a paused download"""
    manager = get_download_manager()
    if manager.resume_download(video_id):
        return {"message": "Download resumed"}
    raise HTTPException(status_code=404, detail="Download not found or not paused")


@router.post("/pause-all")
async def pause_all():
    """Pause all downloads"""
    manager = get_download_manager()
    manager.pause_all()
    return {"message": "All downloads paused"}


@router.post("/resume-all")
async def resume_all():
    """Resume all downloads"""
    manager = get_download_manager()
    manager.resume_all()
    return {"message": "All downloads resumed"}


@router.delete("")
async def clear_completed():
    """Clear completed downloads from queue"""
    manager = get_download_manager()
    cleared = manager.clear_completed()
    return {"cleared": cleared}
