"""
Pydantic schemas for NAS API endpoints.
"""
from datetime import datetime
from pydantic import BaseModel, Field


class NasFolder(BaseModel):
    """NAS folder information"""
    name: str
    path: str
    file_count: int = 0
    folder_count: int = 0
    children: list["NasFolder"] = Field(default_factory=list)


class NasFile(BaseModel):
    """NAS file information"""
    name: str
    path: str
    size_mb: float
    modified_at: datetime
    has_metadata: bool = False


class NasFolderTreeResponse(BaseModel):
    """Response for GET /api/nas/folders"""
    root: NasFolder


class NasFileListResponse(BaseModel):
    """Response for GET /api/nas/files"""
    path: str
    total: int
    files: list[NasFile]
