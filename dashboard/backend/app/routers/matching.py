"""
Matching API endpoints.
Handles 1:N relationship queries (NAS File → Sheet Records → UDM Segments).
"""
from fastapi import APIRouter, HTTPException, Query

from ..schemas.matching import (
    MatchingMatrixResponse,
    MatchingStats,
    FileSegmentsResponse,
    SegmentDetail,
    TimeRange,
    SegmentMetadata,
)
from ..services.mock_data import MockDataService

router = APIRouter(prefix="/matching", tags=["matching"])
mock_service = MockDataService()


@router.get("/matrix", response_model=MatchingMatrixResponse)
async def get_matching_matrix(
    status: str | None = Query(None, description="Filter by status"),
    search: str | None = Query(None, description="Search by file name"),
):
    """
    Get matching matrix showing 1:N relationship between NAS files and segments.

    Returns:
        MatchingMatrixResponse: List of files with their segments
    """
    items = mock_service.get_matching_items(status_filter=status, search=search)

    # Calculate totals
    total_files = len(mock_service._files)
    total_segments = sum(f["segment_count"] for f in mock_service._files)
    matched_files = sum(1 for f in mock_service._files if f["segment_count"] > 0)
    matched_segments = sum(f["udm_count"] for f in mock_service._files)
    unmatched_nas = sum(1 for f in mock_service._files if f["segment_count"] == 0)
    orphan_records = 5  # Mock value

    return MatchingMatrixResponse(
        total_files=total_files,
        total_segments=total_segments,
        matched_files=matched_files,
        matched_segments=matched_segments,
        orphan_records=orphan_records,
        unmatched_nas=unmatched_nas,
        items=items,
    )


@router.get("/stats", response_model=MatchingStats)
async def get_matching_stats():
    """
    Get matching statistics including 1:N relationship metrics.

    Returns:
        MatchingStats: Comprehensive statistics
    """
    stats = mock_service.get_stats()
    return MatchingStats(**stats)


@router.get("/file/{file_name}/segments", response_model=FileSegmentsResponse)
async def get_file_segments(file_name: str):
    """
    Get all segments for a specific file (1:N relationship detail).

    Args:
        file_name: Name of the NAS file

    Returns:
        FileSegmentsResponse: File info with all segments
    """
    file_data = mock_service.get_file_segments(file_name)

    if not file_data:
        raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")

    # Convert segments to SegmentDetail format
    segments_detail = []
    for i, segment in enumerate(file_data["segments"]):
        detail = SegmentDetail(
            index=i + 1,
            source=segment.source,
            row_number=segment.row_number,
            time_range=TimeRange(
                in_tc=segment.time_in,
                out_tc=segment.time_out,
                in_sec=segment.time_in_sec,
                out_sec=segment.time_out_sec,
                duration_sec=segment.duration_sec,
            ),
            metadata=SegmentMetadata(
                rating=segment.rating,
                winner=segment.winner,
                hands=segment.hands,
                tags=segment.tags,
            ),
            udm=segment.udm,
        )
        segments_detail.append(detail)

    return FileSegmentsResponse(
        file_name=file_name,
        nas=file_data["nas"],
        total_segments=file_data["segment_count"],
        converted_segments=file_data["udm_count"],
        segments=segments_detail,
    )
