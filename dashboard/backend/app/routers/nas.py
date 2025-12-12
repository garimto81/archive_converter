"""
NAS API endpoints.
Provides folder tree and file listing functionality.
"""
from fastapi import APIRouter, Query, HTTPException

from ..config import settings
from ..schemas.nas import NasFolderTreeResponse, NasFileListResponse

# Mock 또는 Real 서비스 선택
if settings.nas_use_real_data:
    from ..services.nas_service import get_nas_service
    data_service = get_nas_service(settings.nas_mount_path)
else:
    from ..services.mock_data import MockDataService
    data_service = MockDataService()

router = APIRouter(prefix="/nas", tags=["nas"])


@router.get("/folders", response_model=NasFolderTreeResponse)
async def get_nas_folders():
    """
    Get NAS folder tree structure.

    Returns:
        NasFolderTreeResponse: Folder hierarchy
    """
    try:
        root = data_service.generate_nas_tree()
        return NasFolderTreeResponse(root=root)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"NAS not accessible: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=NasFileListResponse)
async def get_nas_files(
    path: str = Query(..., description="Folder path to list files from"),
):
    """
    Get file list from a specific NAS folder.

    Args:
        path: Folder path (e.g., Z:\\ARCHIVE\\WSOP)

    Returns:
        NasFileListResponse: List of files in the folder
    """
    try:
        files = data_service.get_files_in_folder(path)

        return NasFileListResponse(
            path=path,
            total=len(files),
            files=files,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_nas_status():
    """
    Get NAS scan status.

    Returns:
        dict: NAS status information
    """
    if settings.nas_use_real_data:
        return data_service.get_scan_status()
    else:
        return {
            "mode": "mock",
            "nas_path": settings.nas_mount_path,
            "message": "Using mock data"
        }


@router.post("/refresh")
async def refresh_nas_scan(
    mode: str = Query("full", description="Scan mode: 'full' or 'incremental'"),
):
    """
    Force refresh NAS scan.

    Args:
        mode: Scan mode
            - "full": Full rescan of all files
            - "incremental": Only scan new/modified files since last scan

    Returns:
        dict: Scan result summary
    """
    if not settings.nas_use_real_data:
        return {"message": "Mock mode - no refresh needed", "mode": mode}

    if mode not in ("full", "incremental"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use 'full' or 'incremental'")

    try:
        stats = data_service.refresh_scan(force=True, mode=mode)
        return {
            "message": "Scan completed",
            "mode": stats.scan_mode,
            "total_files": stats.video_files,
            "total_size_gb": round(stats.total_size_gb, 2),
            "scan_duration_sec": round(stats.scan_duration_sec, 2),
            "new_files": stats.new_files,
            "modified_files": stats.modified_files,
            "brand_counts": stats.brand_counts,
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"NAS not accessible: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
