"""
Matching API endpoints.
Handles 1:N relationship queries (NAS File → Sheet Records → UDM Segments).
"""
from fastapi import APIRouter, HTTPException, Query

from ..config import settings
from ..schemas.matching import (
    MatchingMatrixResponse,
    MatchingStats,
    FileSegmentsResponse,
    SegmentDetail,
    TimeRange,
    SegmentMetadata,
)

# Mock 또는 Real 서비스 선택
if settings.nas_use_real_data:
    from ..services.nas_service import get_nas_service
    data_service = get_nas_service(settings.nas_mount_path)
else:
    from ..services.mock_data import MockDataService
    data_service = MockDataService()

router = APIRouter(prefix="/matching", tags=["matching"])


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
    try:
        items = data_service.get_matching_items(status_filter=status, search=search)

        # Calculate totals
        if settings.nas_use_real_data:
            stats = data_service.get_stats()
            total_files = stats["sources"]["nas"]["total_files"]
            total_segments = stats["matching"]["segments"]["total"]
            matched_files = stats["matching"]["files"]["total_with_metadata"]
            matched_segments = stats["matching"]["segments"]["complete"]
            unmatched_nas = stats["matching"]["files"]["unmatched"]
            orphan_records = stats["matching"]["orphan_records"]
        else:
            total_files = len(data_service._files)
            total_segments = sum(f["segment_count"] for f in data_service._files)
            matched_files = sum(1 for f in data_service._files if f["segment_count"] > 0)
            matched_segments = sum(f["udm_count"] for f in data_service._files)
            unmatched_nas = sum(1 for f in data_service._files if f["segment_count"] == 0)
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
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"NAS not accessible: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=MatchingStats)
async def get_matching_stats():
    """
    Get matching statistics including 1:N relationship metrics.

    Returns:
        MatchingStats: Comprehensive statistics
    """
    try:
        stats = data_service.get_stats()
        return MatchingStats(**stats)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=f"NAS not accessible: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_name}/segments", response_model=FileSegmentsResponse)
async def get_file_segments(file_name: str):
    """
    Get all segments for a specific file (1:N relationship detail).

    Args:
        file_name: Name of the NAS file

    Returns:
        FileSegmentsResponse: File info with all segments
    """
    try:
        file_data = data_service.get_file_segments(file_name)

        if not file_data:
            raise HTTPException(status_code=404, detail=f"File '{file_name}' not found")

        # Convert segments to SegmentDetail format
        segments_detail = []
        for i, segment in enumerate(file_data.get("segments", [])):
            # Handle both dict and SegmentRecord object
            if hasattr(segment, "source"):
                # SegmentRecord object
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
            else:
                # Dict format (from real NAS service)
                detail = SegmentDetail(
                    index=i + 1,
                    source=segment.get("source", "unknown"),
                    row_number=segment.get("row_number", i + 1),
                    time_range=TimeRange(
                        in_tc=segment.get("time_in", "00:00:00"),
                        out_tc=segment.get("time_out", "00:00:00"),
                        in_sec=segment.get("time_in_sec", 0.0),
                        out_sec=segment.get("time_out_sec", 0.0),
                        duration_sec=segment.get("duration_sec", 0.0),
                    ),
                    metadata=SegmentMetadata(
                        rating=segment.get("rating"),
                        winner=segment.get("winner"),
                        hands=segment.get("hands"),
                        tags=segment.get("tags", []),
                    ),
                    udm=segment.get("udm"),
                )
            segments_detail.append(detail)

        # Handle nas field (dict or NasFileInfo)
        nas_data = file_data.get("nas")
        if isinstance(nas_data, dict):
            from ..schemas.matching import NasFileInfo
            nas_info = NasFileInfo(**nas_data)
        else:
            nas_info = nas_data

        return FileSegmentsResponse(
            file_name=file_name,
            nas=nas_info,
            total_segments=file_data.get("segment_count", 0),
            converted_segments=file_data.get("udm_count", 0),
            segments=segments_detail,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
