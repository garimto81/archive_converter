"""PokerGO Downloader Web API"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import videos, downloads, hls, settings as settings_router, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    print(f"Database: {settings.database_path}")
    print(f"Downloads: {settings.download_path}")

    # Ensure directories exist
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    settings.download_path.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="PokerGO Video Downloader Web API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])
app.include_router(downloads.router, prefix="/api/downloads", tags=["Downloads"])
app.include_router(hls.router, prefix="/api/hls", tags=["HLS"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
