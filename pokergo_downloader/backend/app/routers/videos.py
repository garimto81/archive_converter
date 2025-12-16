"""Videos API Router"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from pathlib import Path
import json

from ..models.video import Video, VideoCreate, VideoUpdate, VideoResponse, VideoStats, VideoStatus
from ..services.database import get_db

router = APIRouter()


@router.get("", response_model=VideoResponse)
async def list_videos(
    query: str = Query("", description="Search query"),
    show: Optional[str] = Query(None, description="Filter by show"),
    year: Optional[int] = Query(None, description="Filter by year"),
    status: Optional[VideoStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
):
    """List videos with filtering and pagination"""
    db = get_db()
    videos = db.search_videos(query=query, show=show, year=year, status=status)

    # Pagination
    total = len(videos)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = videos[start:end]

    return VideoResponse(
        total=total,
        videos=[_to_pydantic(v) for v in paginated],
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=VideoStats)
async def get_stats():
    """Get video statistics"""
    db = get_db()
    all_videos = db.get_all_videos()

    stats = {
        "total": len(all_videos),
        "pending": 0,
        "downloading": 0,
        "completed": 0,
        "failed": 0,
        "total_size": 0,
    }

    for v in all_videos:
        stats[v.status.value] = stats.get(v.status.value, 0) + 1
        stats["total_size"] += v.file_size

    return VideoStats(
        **stats,
        shows=db.get_unique_shows(),
        years=db.get_unique_years(),
    )


@router.get("/{video_id}", response_model=Video)
async def get_video(video_id: str):
    """Get a single video by ID"""
    db = get_db()
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return _to_pydantic(video)


@router.post("", response_model=Video)
async def create_video(video: VideoCreate):
    """Create a new video"""
    db = get_db()

    from ...models.video import Video as DBVideo

    db_video = DBVideo(
        id=video.id,
        title=video.title,
        show=video.show,
        url=video.url,
        thumbnail_url=video.thumbnail_url,
        season=video.season,
        episode=video.episode,
        year=video.year,
        duration=video.duration,
        duration_str=video.duration_str,
        hls_url=video.hls_url,
    )

    if not db.insert_video(db_video):
        raise HTTPException(status_code=409, detail="Video already exists")

    return _to_pydantic(db_video)


@router.patch("/{video_id}", response_model=Video)
async def update_video(video_id: str, update: VideoUpdate):
    """Update a video"""
    db = get_db()
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # Apply updates
    if update.title is not None:
        video.title = update.title
    if update.hls_url is not None:
        video.hls_url = update.hls_url
    if update.status is not None:
        from ...models.video import VideoStatus as DBVideoStatus
        video.status = DBVideoStatus(update.status.value)
    if update.file_path is not None:
        video.file_path = update.file_path
    if update.file_size is not None:
        video.file_size = update.file_size
    if update.progress is not None:
        video.progress = update.progress
    if update.error_message is not None:
        video.error_message = update.error_message

    db.update_video(video)
    return _to_pydantic(video)


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete a video"""
    db = get_db()
    video = db.get_video(video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # TODO: Implement delete in database
    return {"message": "Video deleted"}


@router.post("/import")
async def import_videos(file: UploadFile = File(...)):
    """Import videos from JSON file"""
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="File must be JSON")

    content = await file.read()
    data = json.loads(content)

    # Handle both flat list and {"videos": [...]} format
    videos_list = data if isinstance(data, list) else data.get("videos", [])

    db = get_db()
    imported = 0

    for v in videos_list:
        video_id = v.get("id") or v.get("url", "").replace("https://www.pokergo.com/videos/", "")
        if not video_id:
            continue

        # Import Video model from core module
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
        from pokergo_downloader.models.video import Video as DBVideo

        db_video = DBVideo(
            id=video_id,
            title=v.get("title", "Unknown"),
            show=v.get("show", "WSOP"),
            url=v.get("url", ""),
            thumbnail_url=v.get("thumbnail_url", ""),
            year=v.get("year"),
            season=v.get("season"),
            episode=v.get("episode"),
            hls_url=v.get("hls_url"),
        )

        if db.insert_video(db_video):
            imported += 1

    return {"imported": imported, "total": len(videos_list)}


@router.get("/export")
async def export_videos(
    show: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[VideoStatus] = None,
):
    """Export videos to JSON"""
    db = get_db()

    filters = {}
    if show:
        filters["show"] = show
    if year:
        filters["year"] = year
    if status:
        filters["status"] = status

    videos = db.search_videos(**filters) if filters else db.get_all_videos()

    return {
        "total": len(videos),
        "videos": [v.to_dict() for v in videos],
    }


def _to_pydantic(db_video) -> Video:
    """Convert database video to Pydantic model"""
    return Video(
        id=db_video.id,
        title=db_video.title,
        show=db_video.show,
        url=db_video.url,
        thumbnail_url=db_video.thumbnail_url,
        season=db_video.season,
        episode=db_video.episode,
        year=db_video.year,
        duration=db_video.duration,
        duration_str=db_video.duration_str,
        hls_url=db_video.hls_url,
        status=VideoStatus(db_video.status.value),
        file_path=db_video.file_path,
        file_size=db_video.file_size,
        progress=db_video.progress,
        error_message=db_video.error_message,
        created_at=db_video.created_at,
        updated_at=db_video.updated_at,
    )
