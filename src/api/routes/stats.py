"""
통계 엔드포인트

대시보드용 통계 정보
"""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(
    prefix="/api/v1/stats",
    tags=["Statistics"],
)


# =============================================================================
# Response Schemas
# =============================================================================


class StatsResponse(BaseModel):
    """통계 응답"""

    assets: dict[str, Any] = Field(
        ..., description="Asset 통계"
    )
    segments: dict[str, Any] = Field(
        ..., description="Segment 통계"
    )
    brands: dict[str, int] = Field(
        ..., description="브랜드별 Asset 수"
    )
    years: dict[int, int] = Field(
        ..., description="연도별 Asset 수"
    )
    rating_distribution: dict[int, int] = Field(
        ..., description="별점 분포 (Segment 기준)"
    )
    top_players: list[dict[str, Any]] = Field(
        ..., description="상위 플레이어 (등장 횟수)"
    )


# =============================================================================
# Stats Endpoints
# =============================================================================


@router.get(
    "",
    response_model=StatsResponse,
    summary="전체 통계",
    description="""
    대시보드용 전체 통계를 반환합니다.

    **포함 정보**:
    - Asset 총 수, 파일 크기 합계, 총 영상 길이
    - Segment 총 수, 평균 길이, 별점 분포
    - 브랜드별/연도별 분포
    - 상위 플레이어 (등장 횟수)
    """,
)
async def get_stats() -> StatsResponse:
    """
    전체 통계

    TODO: DB 집계 쿼리 구현
    """
    # MOCK RESPONSE
    return StatsResponse(
        assets={
            "total_count": 0,
            "total_size_bytes": 0,
            "total_duration_sec": 0,
        },
        segments={
            "total_count": 0,
            "avg_duration_sec": 0,
            "avg_rating": 0,
        },
        brands={
            "WSOP": 0,
            "HCL": 0,
            "PAD": 0,
        },
        years={
            2024: 0,
            2023: 0,
        },
        rating_distribution={
            5: 0,
            4: 0,
            3: 0,
            2: 0,
            1: 0,
            0: 0,
        },
        top_players=[],
    )


@router.get(
    "/brand/{brand}",
    summary="브랜드별 통계",
    description="특정 브랜드의 상세 통계를 반환합니다.",
)
async def get_brand_stats(brand: str) -> dict:
    """
    브랜드별 통계

    TODO: DB 집계 쿼리 구현
    """
    return {
        "brand": brand,
        "asset_count": 0,
        "segment_count": 0,
        "years": {},
    }


@router.get(
    "/year/{year}",
    summary="연도별 통계",
    description="특정 연도의 상세 통계를 반환합니다.",
)
async def get_year_stats(year: int) -> dict:
    """
    연도별 통계

    TODO: DB 집계 쿼리 구현
    """
    return {
        "year": year,
        "asset_count": 0,
        "segment_count": 0,
        "brands": {},
    }
