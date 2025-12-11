"""
API 예외 처리

커스텀 예외 클래스 및 핸들러
"""

from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


# =============================================================================
# Custom Exceptions
# =============================================================================


class ResourceNotFoundError(HTTPException):
    """리소스를 찾을 수 없음"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "RESOURCE_NOT_FOUND",
                "message": f"{resource_type} not found: {resource_id}",
                "resource_type": resource_type,
                "resource_id": resource_id,
            },
        )


class ValidationError(HTTPException):
    """데이터 검증 실패"""

    def __init__(self, field: str, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "VALIDATION_ERROR",
                "message": message,
                "field": field,
                "details": details or {},
            },
        )


class ConflictError(HTTPException):
    """리소스 충돌 (중복 등)"""

    def __init__(self, message: str, details: dict = None):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "CONFLICT",
                "message": message,
                "details": details or {},
            },
        )


class InternalServerError(HTTPException):
    """서버 내부 오류"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": message,
            },
        )


# =============================================================================
# Exception Handlers
# =============================================================================


async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    """HTTPException 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": getattr(exc.detail, "error", "HTTP_ERROR"),
            "message": (
                exc.detail.get("message")
                if isinstance(exc.detail, dict)
                else str(exc.detail)
            ),
            "details": (
                exc.detail if isinstance(exc.detail, dict) else None
            ),
            "path": str(request.url),
        },
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Pydantic ValidationError 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": str(exc),
            "path": str(request.url),
        },
    )


async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """일반 예외 핸들러"""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": str(exc),
            "path": str(request.url),
        },
    )
