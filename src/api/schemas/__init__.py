"""
API Response/Request Schemas

Pydantic V2 기반 DTO 정의
UDM 모델과 API 레이어 분리
"""

from .asset import (
    AssetCreateRequest,
    AssetResponse,
    AssetUpdateRequest,
    AssetListResponse,
)
from .common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    MessageResponse,
)
from .export import (
    ExportJSONRequest,
    ExportCSVRequest,
    ExportResponse,
)
from .search import (
    SearchParams,
    SearchResponse,
)
from .segment import (
    SegmentCreateRequest,
    SegmentResponse,
    SegmentUpdateRequest,
    SegmentListResponse,
)

__all__ = [
    # Asset
    "AssetCreateRequest",
    "AssetResponse",
    "AssetUpdateRequest",
    "AssetListResponse",
    # Segment
    "SegmentCreateRequest",
    "SegmentResponse",
    "SegmentUpdateRequest",
    "SegmentListResponse",
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "MessageResponse",
    # Export
    "ExportJSONRequest",
    "ExportCSVRequest",
    "ExportResponse",
    # Search
    "SearchParams",
    "SearchResponse",
]
