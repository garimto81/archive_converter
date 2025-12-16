"""
FastAPI 공통 의존성

DB 세션, 페이징, 인증 등
"""

from typing import Annotated

from fastapi import Query

from .schemas.common import PaginationParams


# =============================================================================
# Pagination Dependency
# =============================================================================


async def get_pagination_params(
    page: Annotated[int, Query(ge=1, description="페이지 번호")] = 1,
    page_size: Annotated[
        int, Query(ge=1, le=1000, description="페이지당 항목 수")
    ] = 50,
) -> PaginationParams:
    """페이징 파라미터 의존성"""
    return PaginationParams(page=page, page_size=page_size)


# =============================================================================
# Common Query Params
# =============================================================================


async def get_sort_params(
    sort_by: Annotated[
        str, Query(description="정렬 필드")
    ] = "created_at",
    sort_order: Annotated[
        str, Query(pattern="^(asc|desc)$", description="정렬 순서")
    ] = "desc",
) -> dict[str, str]:
    """정렬 파라미터"""
    return {"sort_by": sort_by, "sort_order": sort_order}


# =============================================================================
# Database Session (향후 구현)
# =============================================================================


# async def get_db_session():
#     """DB 세션 제공 (SQLAlchemy/MongoDB)"""
#     # TODO: DB 연결 구현 후 활성화
#     pass


# =============================================================================
# Authentication (향후 구현)
# =============================================================================


# async def get_current_user(
#     token: Annotated[str, Depends(oauth2_scheme)]
# ):
#     """현재 인증된 사용자 정보"""
#     # TODO: JWT 검증 구현
#     pass


# =============================================================================
# Rate Limiting (향후 구현)
# =============================================================================


# async def rate_limiter():
#     """API 속도 제한"""
#     # TODO: Redis 기반 rate limiting
#     pass
