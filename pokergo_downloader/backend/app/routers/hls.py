"""HLS URL Fetching Router"""

from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..services.database import get_db
from ..services.hls_fetcher import get_hls_fetcher

router = APIRouter()


class FetchRequest:
    """HLS fetch request"""
    video_ids: List[str]


@router.post("/fetch")
async def fetch_hls_urls(video_ids: List[str], background_tasks: BackgroundTasks):
    """Start fetching HLS URLs for videos"""
    fetcher = get_hls_fetcher()

    if fetcher.is_running:
        raise HTTPException(status_code=409, detail="Fetch already in progress")

    # Start fetch in background
    background_tasks.add_task(fetcher.fetch_batch, video_ids)

    return {
        "message": "Fetch started",
        "total": len(video_ids),
    }


@router.get("/status")
async def get_fetch_status():
    """Get current fetch status"""
    fetcher = get_hls_fetcher()

    return {
        "is_running": fetcher.is_running,
        "current_video": fetcher.current_video,
        "progress": fetcher.progress,
        "total": fetcher.total,
        "completed": fetcher.completed,
        "failed": fetcher.failed,
    }


@router.post("/cancel")
async def cancel_fetch():
    """Cancel ongoing fetch"""
    fetcher = get_hls_fetcher()

    if not fetcher.is_running:
        raise HTTPException(status_code=400, detail="No fetch in progress")

    fetcher.cancel()
    return {"message": "Fetch cancelled"}


@router.get("/missing")
async def get_videos_without_hls():
    """Get list of videos without HLS URLs"""
    db = get_db()
    all_videos = db.get_all_videos()

    missing = [v for v in all_videos if not v.hls_url]

    return {
        "total": len(missing),
        "videos": [{"id": v.id, "title": v.title, "url": v.url} for v in missing],
    }
