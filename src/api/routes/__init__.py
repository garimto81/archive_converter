"""
API 라우트 모듈

각 엔드포인트별 라우터 정의
"""

from .assets import router as assets_router
from .export import router as export_router
from .search import router as search_router
from .segments import router as segments_router
from .stats import router as stats_router

__all__ = [
    "assets_router",
    "segments_router",
    "search_router",
    "export_router",
    "stats_router",
]
