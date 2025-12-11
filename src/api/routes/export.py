"""
Export 엔드포인트

PRD-0005-EXPORT-AGENT 기반 데이터 출력
"""

import time
from typing import Annotated

from fastapi import APIRouter, Body
from fastapi.responses import StreamingResponse

from ..schemas import (
    ExportCSVRequest,
    ExportJSONRequest,
    ExportResponse,
)

router = APIRouter(
    prefix="/api/v1/export",
    tags=["Export"],
)


# =============================================================================
# JSON Export
# =============================================================================


@router.post(
    "/json",
    response_model=ExportResponse,
    summary="JSON 내보내기",
    description="""
    UDM 데이터를 JSON 형식으로 내보냅니다.

    **출력 형식**:
    ```json
    {
      "_metadata": {
        "exported_at": "2025-12-11T14:30:00Z",
        "schema_version": "3.0.0"
      },
      "assets": [...]
    }
    ```

    **옵션**:
    - pretty_print: JSON 포맷팅 (indent=2)
    - include_metadata: 메타데이터 포함
    - include_segments: Segment 데이터 포함
    """,
)
async def export_json(
    request: Annotated[
        ExportJSONRequest,
        Body(description="JSON Export 설정"),
    ],
) -> ExportResponse:
    """
    JSON 내보내기

    TODO: Export Agent 연동
    """
    start_time = time.time()

    # MOCK RESPONSE
    execution_time_ms = int((time.time() - start_time) * 1000)

    return ExportResponse(
        success=True,
        format=request.format,
        records_exported=0,
        file_size_bytes=0,
        download_url="/downloads/temp_export.json",
        expires_at="2025-12-11T15:00:00Z",
        execution_time_ms=execution_time_ms,
        metadata={
            "pretty_print": request.pretty_print,
            "include_segments": request.include_segments,
        },
    )


@router.post(
    "/json/stream",
    response_class=StreamingResponse,
    summary="JSON 스트리밍 다운로드",
    description="JSON 파일을 직접 스트리밍하여 다운로드합니다 (대용량 처리).",
)
async def export_json_stream(
    request: ExportJSONRequest,
) -> StreamingResponse:
    """
    JSON 스트리밍 다운로드

    TODO: 스트리밍 구현
    """
    import io
    import json

    # MOCK: Empty JSON
    data = {"_metadata": {}, "assets": []}
    json_str = json.dumps(
        data, indent=2 if request.pretty_print else None, ensure_ascii=False
    )
    buffer = io.BytesIO(json_str.encode("utf-8"))

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": "attachment; filename=export.json"
        },
    )


# =============================================================================
# CSV Export
# =============================================================================


@router.post(
    "/csv",
    response_model=ExportResponse,
    summary="CSV 내보내기",
    description="""
    UDM 데이터를 CSV 형식으로 평면화하여 내보냅니다.

    **평면화 규칙**:
    - 배열 필드 (players, tags): array_delimiter로 구분 (기본: "|")
    - 중첩 객체 (event_context): Dot notation (event_year, event_brand)

    **옵션**:
    - delimiter: 필드 구분자 (기본: ",")
    - array_delimiter: 배열 요소 구분자 (기본: "|")
    - encoding: 파일 인코딩 (기본: "utf-8-sig" - Excel BOM)
    - columns: 출력할 컬럼 목록 (지정하지 않으면 전체)

    **Excel 호환**:
    - encoding="utf-8-sig" (BOM 포함)
    - delimiter="," (기본)
    """,
)
async def export_csv(
    request: Annotated[
        ExportCSVRequest,
        Body(description="CSV Export 설정"),
    ],
) -> ExportResponse:
    """
    CSV 내보내기

    TODO: Export Agent 연동
    """
    start_time = time.time()

    # MOCK RESPONSE
    execution_time_ms = int((time.time() - start_time) * 1000)

    return ExportResponse(
        success=True,
        format=request.format,
        records_exported=0,
        file_size_bytes=0,
        download_url="/downloads/temp_export.csv",
        expires_at="2025-12-11T15:00:00Z",
        execution_time_ms=execution_time_ms,
        metadata={
            "delimiter": request.delimiter,
            "array_delimiter": request.array_delimiter,
            "encoding": request.encoding,
        },
    )


@router.post(
    "/csv/stream",
    response_class=StreamingResponse,
    summary="CSV 스트리밍 다운로드",
    description="CSV 파일을 직접 스트리밍하여 다운로드합니다.",
)
async def export_csv_stream(
    request: ExportCSVRequest,
) -> StreamingResponse:
    """
    CSV 스트리밍 다운로드

    TODO: 스트리밍 구현
    """
    import io

    # MOCK: Empty CSV
    csv_str = "asset_uuid,file_name,event_year\n"
    buffer = io.BytesIO(csv_str.encode(request.encoding))

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )
