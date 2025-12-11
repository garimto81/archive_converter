"""
NAS API endpoints.
Provides folder tree and file listing functionality.
"""
from fastapi import APIRouter, Query

from ..schemas.nas import NasFolderTreeResponse, NasFileListResponse
from ..services.mock_data import MockDataService

router = APIRouter(prefix="/nas", tags=["nas"])
mock_service = MockDataService()


@router.get("/folders", response_model=NasFolderTreeResponse)
async def get_nas_folders():
    """
    Get NAS folder tree structure.

    Returns:
        NasFolderTreeResponse: Folder hierarchy
    """
    root = mock_service.generate_nas_tree()
    return NasFolderTreeResponse(root=root)


@router.get("/files", response_model=NasFileListResponse)
async def get_nas_files(
    path: str = Query(..., description="Folder path to list files from"),
):
    """
    Get file list from a specific NAS folder.

    Args:
        path: Folder path (e.g., /ARCHIVE/WSOP/STREAM)

    Returns:
        NasFileListResponse: List of files in the folder
    """
    files = mock_service.get_files_in_folder(path)

    return NasFileListResponse(
        path=path,
        total=len(files),
        files=files,
    )
