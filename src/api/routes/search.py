"""
검색/필터 엔드포인트

복합 검색 및 고급 필터링
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from ..schemas import SearchParams, SearchResponse

router = APIRouter(
    prefix="/api/v1/search",
    tags=["Search"],
)


# =============================================================================
# Search
# =============================================================================


@router.get(
    "",
    response_model=SearchResponse,
    summary="통합 검색",
    description="""
    Asset과 Segment를 통합 검색합니다.

    **검색 필드**:
    - q: 전문 검색 (파일명, 플레이어명, 설명)
    - brand, year, location: 이벤트 필터
    - rating_min/max: 별점 범위
    - player_name: 특정 플레이어 포함
    - tags: 태그 필터 (OR 조건)

    **Segment 전용 필터**:
    - has_cooler: 쿨러 핸드
    - has_badbeat: 배드비트
    - has_allin_preflop: 프리플랍 올인

    **정렬**:
    - sort_by: rating (기본), duration_sec, created_at
    - sort_order: desc (기본), asc

    **반환**:
    - Asset + Segment 통합 결과
    - relevance_score: 검색 관련도 (0.0-1.0)
    """,
)
async def search(
    params: Annotated[SearchParams, Depends()],
) -> SearchResponse:
    """
    통합 검색

    TODO: DB 검색 구현 (Elasticsearch 또는 Full-Text Search)
    """
    import time

    start_time = time.time()

    # MOCK RESPONSE
    results = []

    # 검색 필터 요약
    filters_applied = {}
    if params.q:
        filters_applied["query"] = params.q
    if params.brand:
        filters_applied["brand"] = params.brand
    if params.year:
        filters_applied["year"] = params.year
    if params.rating_min:
        filters_applied["rating_min"] = params.rating_min

    query_time_ms = int((time.time() - start_time) * 1000)

    return SearchResponse(
        results=results,
        total=0,
        page=params.page,
        page_size=params.page_size,
        query_time_ms=query_time_ms,
        filters_applied=filters_applied,
    )
