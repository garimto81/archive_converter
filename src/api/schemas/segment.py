"""
Segment API 스키마

Segment CRUD용 Request/Response DTO
"""

from typing import Annotated, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ...models.udm import (
    AllInStage,
    GameType,
    PlayerInHand,
    SegmentType,
    SituationFlags,
)


# =============================================================================
# Request Schemas
# =============================================================================


class SegmentCreateRequest(BaseModel):
    """Segment 생성 요청"""

    # parent_asset_uuid는 URL path에서 제공
    segment_type: SegmentType = Field(default=SegmentType.HAND)
    time_in_sec: Annotated[float, Field(ge=0, description="시작 시간 (초)")]
    time_out_sec: Annotated[float, Field(ge=0, description="종료 시간 (초)")]
    title: Optional[str] = None
    game_type: GameType = Field(default=GameType.TOURNAMENT)
    rating: Optional[int] = Field(default=None, ge=0, le=5)
    winner: Optional[str] = None
    winning_hand: Optional[str] = None
    losing_hand: Optional[str] = None
    players: Optional[list[PlayerInHand]] = None
    tags_action: Optional[list[str]] = None
    tags_emotion: Optional[list[str]] = None
    tags_content: Optional[list[str]] = None
    situation_flags: Optional[SituationFlags] = None
    all_in_stage: Optional[AllInStage] = None
    board: Optional[str] = None
    description: Optional[str] = None


class SegmentUpdateRequest(BaseModel):
    """Segment 수정 요청 (부분 업데이트)"""

    time_in_sec: Optional[float] = Field(default=None, ge=0)
    time_out_sec: Optional[float] = Field(default=None, ge=0)
    title: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=0, le=5)
    winner: Optional[str] = None
    winning_hand: Optional[str] = None
    losing_hand: Optional[str] = None
    players: Optional[list[PlayerInHand]] = None
    tags_action: Optional[list[str]] = None
    tags_emotion: Optional[list[str]] = None
    tags_content: Optional[list[str]] = None
    situation_flags: Optional[SituationFlags] = None
    all_in_stage: Optional[AllInStage] = None
    board: Optional[str] = None
    description: Optional[str] = None


# =============================================================================
# Response Schemas
# =============================================================================


class SegmentResponse(BaseModel):
    """Segment 응답"""

    segment_uuid: UUID
    parent_asset_uuid: UUID
    segment_type: SegmentType
    time_in_sec: float
    time_out_sec: float
    duration_sec: float = Field(..., description="계산된 길이")
    title: Optional[str] = None
    game_type: GameType
    rating: Optional[int] = None
    winner: Optional[str] = None
    winning_hand: Optional[str] = None
    losing_hand: Optional[str] = None
    players: Optional[list[PlayerInHand]] = None
    tags_action: Optional[list[str]] = None
    tags_emotion: Optional[list[str]] = None
    tags_content: Optional[list[str]] = None
    situation_flags: Optional[SituationFlags] = None
    all_in_stage: Optional[AllInStage] = None
    board: Optional[str] = None
    description: Optional[str] = None


class SegmentListItem(BaseModel):
    """Segment 목록 항목 (경량화)"""

    segment_uuid: UUID
    parent_asset_uuid: UUID
    segment_type: SegmentType
    time_in_sec: float
    time_out_sec: float
    duration_sec: float
    rating: Optional[int] = None
    winner: Optional[str] = None
    players_count: int = Field(default=0, description="참여 플레이어 수")


class SegmentListResponse(BaseModel):
    """Segment 목록 응답"""

    items: list[SegmentListItem]
    total: int
    page: int
    page_size: int
