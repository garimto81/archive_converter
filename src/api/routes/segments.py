"""
Segment CRUD 엔드포인트
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, status

from ..dependencies import get_pagination_params
from ..exceptions import ResourceNotFoundError
from ..schemas import (
    MessageResponse,
    PaginationParams,
    SegmentCreateRequest,
    SegmentListResponse,
    SegmentResponse,
    SegmentUpdateRequest,
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Segments"],
)


# =============================================================================
# Segment CRUD
# =============================================================================


@router.post(
    "/assets/{asset_uuid}/segments",
    response_model=SegmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Segment 생성",
    description="""
    특정 Asset에 새로운 Segment를 생성합니다.

    **필수 필드**:
    - time_in_sec: 시작 시간
    - time_out_sec: 종료 시간 (time_in_sec보다 커야 함)

    **검증**:
    - BR-001: time_out_sec > time_in_sec
    - BR-003: 권장 핸드 길이 10-3600초 (경고만)
    """,
)
async def create_segment(
    asset_uuid: Annotated[UUID, Path(description="부모 Asset UUID")],
    segment: SegmentCreateRequest,
) -> SegmentResponse:
    """
    Segment 생성

    TODO: DB 저장 구현
    """
    # MOCK RESPONSE
    from uuid import uuid4

    from ...models.udm import Segment

    # Create Segment
    new_segment = Segment(
        segment_uuid=uuid4(),
        parent_asset_uuid=asset_uuid,
        segment_type=segment.segment_type,
        time_in_sec=segment.time_in_sec,
        time_out_sec=segment.time_out_sec,
        title=segment.title,
        game_type=segment.game_type,
        rating=segment.rating,
        winner=segment.winner,
        winning_hand=segment.winning_hand,
        losing_hand=segment.losing_hand,
        players=segment.players,
        tags_action=segment.tags_action,
        tags_emotion=segment.tags_emotion,
        tags_content=segment.tags_content,
        situation_flags=segment.situation_flags,
        all_in_stage=segment.all_in_stage,
        board=segment.board,
        description=segment.description,
    )

    return SegmentResponse(
        segment_uuid=new_segment.segment_uuid,
        parent_asset_uuid=new_segment.parent_asset_uuid,
        segment_type=new_segment.segment_type,
        time_in_sec=new_segment.time_in_sec,
        time_out_sec=new_segment.time_out_sec,
        duration_sec=new_segment.duration_sec,
        title=new_segment.title,
        game_type=new_segment.game_type,
        rating=new_segment.rating,
        winner=new_segment.winner,
        winning_hand=new_segment.winning_hand,
        losing_hand=new_segment.losing_hand,
        players=new_segment.players,
        tags_action=new_segment.tags_action,
        tags_emotion=new_segment.tags_emotion,
        tags_content=new_segment.tags_content,
        situation_flags=new_segment.situation_flags,
        all_in_stage=new_segment.all_in_stage,
        board=new_segment.board,
        description=new_segment.description,
    )


@router.get(
    "/segments/{segment_uuid}",
    response_model=SegmentResponse,
    summary="Segment 상세 조회",
)
async def get_segment(
    segment_uuid: Annotated[UUID, Path(description="Segment UUID")],
) -> SegmentResponse:
    """
    Segment 상세 조회

    TODO: DB 조회 구현
    """
    raise ResourceNotFoundError("Segment", str(segment_uuid))


@router.put(
    "/segments/{segment_uuid}",
    response_model=SegmentResponse,
    summary="Segment 수정",
    description="Segment 정보를 부분적으로 수정합니다.",
)
async def update_segment(
    segment_uuid: Annotated[UUID, Path(description="Segment UUID")],
    updates: SegmentUpdateRequest,
) -> SegmentResponse:
    """
    Segment 수정

    TODO: DB 업데이트 구현
    """
    raise ResourceNotFoundError("Segment", str(segment_uuid))


@router.delete(
    "/segments/{segment_uuid}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Segment 삭제",
)
async def delete_segment(
    segment_uuid: Annotated[UUID, Path(description="Segment UUID")],
) -> MessageResponse:
    """
    Segment 삭제

    TODO: DB 삭제 구현
    """
    raise ResourceNotFoundError("Segment", str(segment_uuid))


# =============================================================================
# Segment 목록 조회
# =============================================================================


@router.get(
    "/segments",
    response_model=SegmentListResponse,
    summary="Segment 목록 조회",
    description="모든 Segment를 페이징하여 조회합니다.",
)
async def list_segments(
    pagination: Annotated[PaginationParams, Depends(get_pagination_params)],
) -> SegmentListResponse:
    """
    Segment 목록

    TODO: DB 조회 구현
    """
    return SegmentListResponse(
        items=[],
        total=0,
        page=pagination.page,
        page_size=pagination.page_size,
    )
