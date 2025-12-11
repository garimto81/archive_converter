"""
Asset CRUD 엔드포인트

RESTful API for Asset management
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, status

from ..dependencies import get_pagination_params, get_sort_params
from ..exceptions import ResourceNotFoundError
from ..schemas import (
    AssetCreateRequest,
    AssetListResponse,
    AssetResponse,
    AssetUpdateRequest,
    MessageResponse,
    PaginationParams,
)

router = APIRouter(
    prefix="/api/v1/assets",
    tags=["Assets"],
)


# =============================================================================
# Asset CRUD
# =============================================================================


@router.get(
    "",
    response_model=AssetListResponse,
    summary="Asset 목록 조회",
    description="""
    Asset 목록을 페이징하여 조회합니다.

    **필터링 옵션**:
    - brand: 브랜드 필터
    - year: 연도 필터
    - asset_type: Asset 유형 필터

    **정렬**:
    - sort_by: created_at (기본), file_name, event_year
    - sort_order: desc (기본), asc
    """,
)
async def list_assets(
    pagination: Annotated[PaginationParams, Depends(get_pagination_params)],
    sort: Annotated[dict, Depends(get_sort_params)],
    brand: Annotated[str | None, Query(description="브랜드 필터")] = None,
    year: Annotated[
        int | None, Query(ge=1970, le=2100, description="연도 필터")
    ] = None,
    asset_type: Annotated[
        str | None, Query(description="Asset 유형 필터")
    ] = None,
) -> AssetListResponse:
    """
    Asset 목록 조회

    TODO: DB 연동 구현
    """
    # MOCK RESPONSE
    return AssetListResponse(
        items=[],
        total=0,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get(
    "/{asset_uuid}",
    response_model=AssetResponse,
    summary="Asset 상세 조회",
    description="UUID로 특정 Asset의 상세 정보를 조회합니다.",
)
async def get_asset(
    asset_uuid: Annotated[
        UUID, Path(description="Asset UUID")
    ],
) -> AssetResponse:
    """
    Asset 상세 조회

    TODO: DB 연동 구현
    """
    # MOCK: 실제로는 DB에서 조회
    raise ResourceNotFoundError("Asset", str(asset_uuid))


@router.post(
    "",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asset 생성",
    description="""
    새로운 Asset을 생성합니다.

    **필수 필드**:
    - file_name: 파일명
    - event_context.year: 연도
    - event_context.brand: 브랜드
    - source_origin: 데이터 출처
    """,
)
async def create_asset(
    asset: AssetCreateRequest,
) -> AssetResponse:
    """
    Asset 생성

    TODO: DB 저장 구현
    """
    # MOCK RESPONSE
    from datetime import datetime
    from uuid import uuid4

    from ...models.udm import Asset, EventContext

    # Create Asset from request
    event_context = EventContext(**asset.event_context.model_dump())
    new_asset = Asset(
        asset_uuid=uuid4(),
        file_name=asset.file_name,
        file_path_rel=asset.file_path_rel,
        file_path_nas=asset.file_path_nas,
        asset_type=asset.asset_type,
        event_context=event_context,
        tech_spec=asset.tech_spec,
        source_origin=asset.source_origin,
        created_at=datetime.utcnow(),
    )

    # Convert to response
    return AssetResponse(
        asset_uuid=new_asset.asset_uuid,
        file_name=new_asset.file_name,
        file_path_rel=new_asset.file_path_rel,
        file_path_nas=new_asset.file_path_nas,
        asset_type=new_asset.asset_type,
        event_context=new_asset.event_context,
        tech_spec=new_asset.tech_spec,
        source_origin=new_asset.source_origin,
        created_at=new_asset.created_at,
        segment_count=0,
    )


@router.put(
    "/{asset_uuid}",
    response_model=AssetResponse,
    summary="Asset 수정",
    description="Asset 정보를 부분적으로 수정합니다 (PATCH 방식).",
)
async def update_asset(
    asset_uuid: Annotated[UUID, Path(description="Asset UUID")],
    updates: AssetUpdateRequest,
) -> AssetResponse:
    """
    Asset 수정

    TODO: DB 업데이트 구현
    """
    # MOCK: 실제로는 DB 업데이트
    raise ResourceNotFoundError("Asset", str(asset_uuid))


@router.delete(
    "/{asset_uuid}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Asset 삭제",
    description="""
    Asset을 삭제합니다.

    **주의**: 연결된 Segment도 함께 삭제됩니다 (CASCADE).
    """,
)
async def delete_asset(
    asset_uuid: Annotated[UUID, Path(description="Asset UUID")],
) -> MessageResponse:
    """
    Asset 삭제 (CASCADE)

    TODO: DB 삭제 구현
    """
    # MOCK: 실제로는 DB에서 삭제
    raise ResourceNotFoundError("Asset", str(asset_uuid))


# =============================================================================
# Asset의 Segments 조회 (Relationship)
# =============================================================================


@router.get(
    "/{asset_uuid}/segments",
    response_model=list,
    summary="Asset의 Segment 목록",
    description="특정 Asset에 속한 모든 Segment를 조회합니다.",
)
async def get_asset_segments(
    asset_uuid: Annotated[UUID, Path(description="Asset UUID")],
) -> list:
    """
    Asset의 Segment 목록

    TODO: DB 조회 구현
    """
    return []
