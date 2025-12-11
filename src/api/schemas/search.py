"""
검색/필터 API 스키마
"""

from typing import Annotated, Optional

from pydantic import BaseModel, Field

from ...models.udm import Brand, GameType, Location


# =============================================================================
# Request Schemas
# =============================================================================


class SearchParams(BaseModel):
    """검색 파라미터"""

    # 전문 검색
    q: Optional[str] = Field(
        default=None,
        min_length=1,
        description="검색어 (파일명, 플레이어명, 설명)",
    )

    # 필터
    brand: Optional[Brand] = Field(
        default=None, description="브랜드 필터"
    )
    year: Optional[int] = Field(
        default=None, ge=1970, le=2100, description="연도 필터"
    )
    location: Optional[Location] = Field(
        default=None, description="장소 필터"
    )
    rating_min: Optional[int] = Field(
        default=None, ge=0, le=5, description="최소 별점"
    )
    rating_max: Optional[int] = Field(
        default=None, ge=0, le=5, description="최대 별점"
    )
    game_type: Optional[GameType] = Field(
        default=None, description="게임 타입"
    )
    player_name: Optional[str] = Field(
        default=None, description="플레이어명 포함"
    )
    tags: Optional[list[str]] = Field(
        default=None, description="태그 필터 (OR 조건)"
    )

    # Segment 전용 필터
    has_cooler: Optional[bool] = Field(
        default=None, description="쿨러 핸드 여부"
    )
    has_badbeat: Optional[bool] = Field(
        default=None, description="배드비트 여부"
    )
    has_allin_preflop: Optional[bool] = Field(
        default=None, description="프리플랍 올인 여부"
    )

    # 시간 범위 필터
    duration_min_sec: Optional[float] = Field(
        default=None, ge=0, description="최소 핸드 길이 (초)"
    )
    duration_max_sec: Optional[float] = Field(
        default=None, ge=0, description="최대 핸드 길이 (초)"
    )

    # 정렬
    sort_by: str = Field(
        default="rating",
        description="정렬 기준 (rating, duration_sec, created_at 등)",
    )
    sort_order: Annotated[
        str,
        Field(pattern="^(asc|desc)$", description="정렬 순서"),
    ] = "desc"

    # 페이징
    page: Annotated[int, Field(ge=1)] = 1
    page_size: Annotated[int, Field(ge=1, le=1000)] = 50


# =============================================================================
# Response Schemas
# =============================================================================


class SearchResult(BaseModel):
    """검색 결과 항목 (Asset + Segment 통합)"""

    # Asset 정보
    asset_uuid: str
    file_name: str
    event_year: int
    event_brand: Brand

    # Segment 정보 (검색 대상이 Segment인 경우)
    segment_uuid: Optional[str] = None
    time_in_sec: Optional[float] = None
    time_out_sec: Optional[float] = None
    duration_sec: Optional[float] = None
    rating: Optional[int] = None
    winner: Optional[str] = None
    players: Optional[list[str]] = None
    tags_action: Optional[list[str]] = None
    tags_emotion: Optional[list[str]] = None

    # 검색 메타
    relevance_score: Optional[float] = Field(
        default=None, description="검색 관련도 점수 (0.0-1.0)"
    )
    match_reason: Optional[str] = Field(
        default=None, description="매칭 이유 (디버깅용)"
    )


class SearchResponse(BaseModel):
    """검색 응답"""

    results: list[SearchResult]
    total: int
    page: int
    page_size: int
    query_time_ms: int = Field(..., description="쿼리 실행 시간 (ms)")
    filters_applied: dict = Field(
        default_factory=dict, description="적용된 필터 요약"
    )
