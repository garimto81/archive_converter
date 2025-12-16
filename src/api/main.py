"""
Archive Converter REST API

FastAPI 애플리케이션 진입점
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from .routes import (
    assets_router,
    export_router,
    search_router,
    segments_router,
    stats_router,
)


# =============================================================================
# Lifespan Events
# =============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # Startup
    print("Archive Converter API starting...")
    # TODO: DB 연결 초기화
    # TODO: 캐시 초기화

    yield

    # Shutdown
    print("Archive Converter API shutting down...")
    # TODO: DB 연결 종료
    # TODO: 리소스 정리


# =============================================================================
# Application Factory
# =============================================================================


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 생성"""

    app = FastAPI(
        title="Archive Converter API",
        description="""
        비디오 아카이브 메타데이터 관리 REST API

        ## Features
        - **Asset CRUD**: 비디오 파일 메타데이터 관리
        - **Segment CRUD**: 포커 핸드 구간 관리
        - **Search**: 복합 검색 및 필터링
        - **Export**: JSON/CSV 데이터 내보내기
        - **Stats**: 대시보드용 통계

        ## UDM Schema
        - Level 1: Asset (물리적 파일)
        - Level 2: Segment (논리적 구간 - 포커 핸드)

        ## API Versioning
        - Current: v1
        - Prefix: `/api/v1`
        """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # =============================================================================
    # Middleware
    # =============================================================================

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: 프로덕션에서는 특정 도메인만 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # =============================================================================
    # Exception Handlers
    # =============================================================================

    from fastapi import HTTPException
    from pydantic import ValidationError

    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # =============================================================================
    # Routers
    # =============================================================================

    app.include_router(assets_router)
    app.include_router(segments_router)
    app.include_router(search_router)
    app.include_router(export_router)
    app.include_router(stats_router)

    # =============================================================================
    # Root Endpoint
    # =============================================================================

    @app.get(
        "/",
        tags=["Root"],
        summary="API 정보",
    )
    async def root():
        """API 정보 반환"""
        return {
            "name": "Archive Converter API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    @app.get(
        "/health",
        tags=["Root"],
        summary="헬스 체크",
    )
    async def health():
        """헬스 체크"""
        return {
            "status": "healthy",
            "api_version": "1.0.0",
            # TODO: DB 상태 확인
        }

    return app


# =============================================================================
# App Instance
# =============================================================================

app = create_app()


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
