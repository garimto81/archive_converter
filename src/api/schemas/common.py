"""
공통 API 스키마

Pagination, Response Wrapper, Error 등
"""

from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, Field, computed_field

T = TypeVar("T")


# =============================================================================
# Pagination
# =============================================================================


class PaginationParams(BaseModel):
    """페이징 파라미터"""

    page: Annotated[int, Field(ge=1, description="페이지 번호 (1부터 시작)")] = 1
    page_size: Annotated[
        int, Field(ge=1, le=1000, description="페이지당 항목 수")
    ] = 50

    @computed_field
    @property
    def offset(self) -> int:
        """DB 쿼리용 offset 계산"""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    """페이지네이션 메타 정보"""

    page: int = Field(..., description="현재 페이지")
    page_size: int = Field(..., description="페이지 크기")
    total_items: int = Field(..., description="전체 항목 수")
    total_pages: int = Field(..., description="전체 페이지 수")
    has_next: bool = Field(..., description="다음 페이지 존재 여부")
    has_prev: bool = Field(..., description="이전 페이지 존재 여부")


class PaginatedResponse(BaseModel, Generic[T]):
    """페이지네이션된 응답"""

    items: list[T] = Field(..., description="데이터 목록")
    pagination: PaginationMeta = Field(..., description="페이지 정보")


# =============================================================================
# Response Wrappers
# =============================================================================


class MessageResponse(BaseModel):
    """단순 메시지 응답"""

    message: str = Field(..., description="응답 메시지")
    detail: dict[str, Any] | None = Field(
        default=None, description="추가 상세 정보"
    )


class ErrorResponse(BaseModel):
    """에러 응답"""

    error: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    details: dict[str, Any] | None = Field(
        default=None, description="상세 정보"
    )
    request_id: str | None = Field(default=None, description="요청 ID")


# =============================================================================
# Filter Base
# =============================================================================


class FilterParams(BaseModel):
    """필터링 공통 파라미터"""

    sort_by: str = Field(
        default="created_at",
        description="정렬 기준 필드",
    )
    sort_order: Annotated[
        str,
        Field(pattern="^(asc|desc)$", description="정렬 순서 (asc/desc)"),
    ] = "desc"
