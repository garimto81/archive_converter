"""Pydantic schemas for API request/response models."""

from .matching import (
    NasFileInfo,
    SegmentRecord,
    ValidationWarning,
    MatchingItem,
    MatchingMatrixResponse,
    MatchingStats,
    FileSegmentsResponse,
)
from .nas import (
    NasFolder,
    NasFile,
    NasFolderTreeResponse,
    NasFileListResponse,
)

__all__ = [
    # Matching schemas
    "NasFileInfo",
    "SegmentRecord",
    "ValidationWarning",
    "MatchingItem",
    "MatchingMatrixResponse",
    "MatchingStats",
    "FileSegmentsResponse",
    # NAS schemas
    "NasFolder",
    "NasFile",
    "NasFolderTreeResponse",
    "NasFileListResponse",
]
