"""
Pydantic schemas for matching API endpoints.
Supports 1:N relationship model (NAS File → Sheet Records → UDM Segments).
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class NasFileInfo(BaseModel):
    """NAS file information (Asset Level)"""
    exists: bool
    path: str
    size_mb: float = Field(description="File size in megabytes")
    duration_sec: float | None = Field(None, description="Video duration in seconds")
    modified_at: datetime
    inferred_brand: str | None = None


class UdmInfo(BaseModel):
    """UDM segment conversion info"""
    uuid: str | None = None
    status: Literal["complete", "pending", "warning", "error"] = "pending"


class SegmentRecord(BaseModel):
    """
    Individual segment record (Segment Level).
    One NAS file can have multiple segments (1:N relationship).
    """
    row_number: int = Field(description="Sheet row number")
    source: Literal["archive_metadata", "iconik_metadata"]

    # Time information
    time_in: str = Field(description="Timecode (HH:MM:SS)")
    time_out: str = Field(description="Timecode (HH:MM:SS)")
    time_in_sec: float = Field(description="Time in seconds")
    time_out_sec: float = Field(description="Time out seconds")
    duration_sec: float = Field(description="Segment duration")

    # Metadata
    rating: int | None = Field(None, ge=1, le=5, description="Hand rating 1-5 stars")
    winner: str | None = None
    hands: str | None = Field(None, description="Poker hands (e.g., AA vs KK)")
    tags: list[str] = Field(default_factory=list)

    # UDM conversion status
    udm: UdmInfo = Field(default_factory=UdmInfo)


class ValidationWarning(BaseModel):
    """Validation warning for a segment"""
    segment_row: int
    type: str
    message: str
    suggested_fix: dict | None = None


class MatchingItem(BaseModel):
    """
    Matching matrix item (Asset Level).
    Represents 1:N relationship between NAS file and segments.
    """
    file_name: str

    # NAS file info (Asset Level - 1 side)
    nas: NasFileInfo | None = None

    # 1:N relationship: segments count
    segment_count: int = Field(0, description="Total sheet records (segments)")
    udm_count: int = Field(0, description="Converted UDM segments")

    # Segments detail (loaded on expand)
    segments: list[SegmentRecord] = Field(default_factory=list)

    # Status
    status: Literal["complete", "partial", "pending", "warning", "no_metadata", "orphan"]
    status_detail: str = Field(description="Status detail (e.g., '15/15', '6/8')")
    warnings: list[ValidationWarning] = Field(default_factory=list)

    # UI state
    is_expanded: bool = False


class MatchingMatrixResponse(BaseModel):
    """Response for GET /api/matching/matrix"""
    total_files: int
    total_segments: int
    matched_files: int
    matched_segments: int
    orphan_records: int
    unmatched_nas: int
    items: list[MatchingItem]


class SourceStats(BaseModel):
    """Statistics for a data source"""
    total_files: int | None = None
    total_records: int | None = None
    unique_files: int | None = None
    total_size_gb: float | None = None
    scanned_at: datetime | None = None
    synced_at: datetime | None = None


class MatchingStatsFiles(BaseModel):
    """File-level matching statistics"""
    complete: int = Field(description="All segments converted")
    partial: int = Field(description="Some segments converted")
    warning: int = Field(description="Has warnings")
    unmatched: int = Field(description="No metadata")
    total_with_metadata: int


class MatchingStatsSegments(BaseModel):
    """Segment-level matching statistics"""
    complete: int
    pending: int
    warning: int
    total: int


class MatchingCoverage(BaseModel):
    """Coverage metrics"""
    archive_to_nas: float = Field(description="Archive Sheet → NAS match rate")
    iconik_to_nas: float = Field(description="Iconik Sheet → NAS match rate")
    nas_to_any_sheet: float = Field(description="NAS → Any Sheet match rate")
    segment_conversion_rate: float = Field(description="Segment UDM conversion rate")


class MatchingSummary(BaseModel):
    """Summary statistics"""
    avg_segments_per_file: float
    max_segments_per_file: int
    min_segments_per_file: int


class MatchingStats(BaseModel):
    """Response for GET /api/matching/stats"""
    sources: dict[str, SourceStats] = Field(
        description="Stats by source (nas, archive_metadata, iconik_metadata)"
    )
    matching: dict[str, MatchingStatsFiles | MatchingStatsSegments | int] = Field(
        description="Matching statistics (files, segments, orphan_records)"
    )
    coverage: MatchingCoverage
    summary: MatchingSummary


class TimeRange(BaseModel):
    """Time range information for a segment"""
    in_tc: str = Field(description="Timecode in")
    out_tc: str = Field(description="Timecode out")
    in_sec: float = Field(description="Time in seconds")
    out_sec: float = Field(description="Time out seconds")
    duration_sec: float


class SegmentMetadata(BaseModel):
    """Metadata for a segment"""
    rating: int | None = None
    winner: str | None = None
    hands: str | None = None
    tags: list[str] = Field(default_factory=list)


class SegmentDetail(BaseModel):
    """Detailed segment information"""
    index: int
    source: Literal["archive_metadata", "iconik_metadata"]
    row_number: int
    time_range: TimeRange
    metadata: SegmentMetadata
    udm: UdmInfo


class FileSegmentsResponse(BaseModel):
    """Response for GET /api/matching/file/{file_name}/segments"""
    file_name: str
    nas: NasFileInfo | None = None
    total_segments: int
    converted_segments: int
    segments: list[SegmentDetail]
