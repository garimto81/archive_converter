"""
Export API 스키마

PRD-0005-EXPORT-AGENT 기반
"""

from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ExportFormat(str, Enum):
    """Export 포맷"""

    JSON = "json"
    JSONL = "jsonl"
    CSV = "csv"


class CSVDelimiter(str, Enum):
    """CSV 구분자"""

    COMMA = ","
    TAB = "\t"
    PIPE = "|"
    SEMICOLON = ";"


# =============================================================================
# Request Schemas
# =============================================================================


class ExportBaseRequest(BaseModel):
    """Export 공통 요청"""

    # 필터 (빈 경우 전체 데이터)
    asset_uuids: Optional[list[str]] = Field(
        default=None, description="특정 Asset만 출력 (지정하지 않으면 전체)"
    )
    segment_uuids: Optional[list[str]] = Field(
        default=None, description="특정 Segment만 출력"
    )

    # 검색 필터 재사용
    brand: Optional[str] = None
    year: Optional[int] = None
    rating_min: Optional[int] = Field(default=None, ge=0, le=5)

    # 메타데이터 옵션
    include_metadata: bool = Field(
        default=True, description="메타데이터 포함 여부"
    )


class ExportJSONRequest(ExportBaseRequest):
    """JSON Export 요청"""

    format: ExportFormat = Field(default=ExportFormat.JSON)
    pretty_print: bool = Field(
        default=True, description="JSON 포맷팅 (indent=2)"
    )
    include_segments: bool = Field(
        default=True, description="Segment 데이터 포함 여부"
    )


class ExportCSVRequest(ExportBaseRequest):
    """CSV Export 요청"""

    format: ExportFormat = Field(default=ExportFormat.CSV)
    delimiter: CSVDelimiter = Field(
        default=CSVDelimiter.COMMA, description="필드 구분자"
    )
    array_delimiter: str = Field(
        default="|", description="배열 요소 구분자 (players, tags 등)"
    )
    include_header: bool = Field(default=True, description="헤더 행 포함")
    encoding: str = Field(
        default="utf-8-sig", description="파일 인코딩 (Excel BOM)"
    )
    columns: Optional[list[str]] = Field(
        default=None,
        description="출력할 컬럼 목록 (지정하지 않으면 전체)",
    )


# =============================================================================
# Response Schemas
# =============================================================================


class ExportResponse(BaseModel):
    """Export 응답"""

    success: bool = Field(..., description="성공 여부")
    format: ExportFormat = Field(..., description="출력 포맷")
    records_exported: int = Field(..., description="출력된 레코드 수")
    file_size_bytes: int = Field(..., description="파일 크기 (bytes)")
    download_url: Optional[str] = Field(
        default=None, description="다운로드 URL (임시)"
    )
    expires_at: Optional[str] = Field(
        default=None, description="다운로드 만료 시간"
    )
    execution_time_ms: int = Field(
        ..., description="실행 시간 (ms)"
    )
    metadata: Optional[dict] = Field(
        default=None, description="Export 메타데이터"
    )


class ExportJobStatus(BaseModel):
    """Export 작업 상태 (비동기 처리용)"""

    job_id: str = Field(..., description="작업 ID")
    status: Annotated[
        str,
        Field(
            pattern="^(pending|processing|completed|failed)$",
            description="작업 상태",
        ),
    ]
    progress: Annotated[
        float, Field(ge=0.0, le=1.0, description="진행률 (0.0-1.0)")
    ]
    records_processed: int = Field(default=0)
    error_message: Optional[str] = None
    result: Optional[ExportResponse] = Field(
        default=None, description="완료 시 결과"
    )
