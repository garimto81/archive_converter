"""
Asset API 스키마

Asset CRUD용 Request/Response DTO
"""

from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.udm import (
    AssetType,
    Brand,
    EventContext,
    EventType,
    FileNameMeta,
    Location,
    TechSpec,
)
from .segment import SegmentResponse


# =============================================================================
# Request Schemas
# =============================================================================


class EventContextInput(BaseModel):
    """EventContext 입력 (필수 필드만)"""

    year: Annotated[int, Field(ge=1970, le=2100)]
    brand: Brand
    event_type: Optional[EventType] = None
    location: Optional[Location] = None
    venue: Optional[str] = None
    event_number: Optional[int] = Field(default=None, ge=1)
    buyin_usd: Optional[int] = Field(default=None, ge=0)
    season: Optional[int] = Field(default=None, ge=1)
    episode: Optional[int] = Field(default=None, ge=1)
    episode_title: Optional[str] = None


class AssetCreateRequest(BaseModel):
    """Asset 생성 요청"""

    file_name: Annotated[str, Field(min_length=1, description="파일명")]
    file_path_rel: Optional[str] = Field(
        default=None, description="NAS 상대 경로"
    )
    file_path_nas: Optional[str] = Field(
        default=None, description="NAS 전체 경로"
    )
    asset_type: AssetType = Field(
        default=AssetType.SUBCLIP, description="Asset 유형"
    )
    event_context: EventContextInput = Field(..., description="이벤트 정보")
    tech_spec: Optional[TechSpec] = Field(
        default=None, description="기술 사양"
    )
    source_origin: Annotated[
        str, Field(min_length=1, description="데이터 출처")
    ]


class AssetUpdateRequest(BaseModel):
    """Asset 수정 요청 (부분 업데이트 허용)"""

    file_name: Optional[str] = None
    file_path_rel: Optional[str] = None
    file_path_nas: Optional[str] = None
    asset_type: Optional[AssetType] = None
    event_context: Optional[EventContextInput] = None
    tech_spec: Optional[TechSpec] = None


# =============================================================================
# Response Schemas
# =============================================================================


class AssetResponse(BaseModel):
    """Asset 상세 응답"""

    asset_uuid: UUID
    file_name: str
    file_path_rel: Optional[str] = None
    file_path_nas: Optional[str] = None
    asset_type: AssetType
    event_context: EventContext
    tech_spec: Optional[TechSpec] = None
    file_name_meta: Optional[FileNameMeta] = None
    source_origin: str
    created_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    segment_count: int = Field(
        default=0, description="포함된 Segment 수"
    )

    # Segments는 별도 엔드포인트로 조회
    # (N+1 문제 방지, 대용량 처리)


class AssetListItem(BaseModel):
    """Asset 목록 항목 (경량화)"""

    asset_uuid: UUID
    file_name: str
    asset_type: AssetType
    event_year: int = Field(..., description="이벤트 연도")
    event_brand: Brand = Field(..., description="브랜드")
    event_location: Optional[Location] = None
    rating_avg: Optional[float] = Field(
        default=None, description="평균 별점 (Segments 기준)"
    )
    segment_count: int = Field(default=0)
    created_at: Optional[datetime] = None


class AssetListResponse(BaseModel):
    """Asset 목록 응답"""

    items: list[AssetListItem]
    total: int
    page: int
    page_size: int


class AssetDetailResponse(AssetResponse):
    """Asset 상세 응답 (Segments 포함)"""

    segments: list[SegmentResponse] = Field(
        default_factory=list, description="포함된 Segments"
    )
