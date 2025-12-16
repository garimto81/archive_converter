"""Settings API Router"""

from fastapi import APIRouter, HTTPException, BackgroundTasks

from ..models.settings import (
    SettingsUpdate,
    SettingsResponse,
    LoginTestRequest,
    LoginTestResponse,
)
from ..services.database import get_db
from ..config import settings as app_settings

router = APIRouter()


@router.get("", response_model=SettingsResponse)
async def get_settings():
    """Get current settings"""
    db = get_db()

    return SettingsResponse(
        pokergo_email=db.get_config("pokergo_email"),
        download_path=db.get_config("download_path", str(app_settings.download_path)),
        video_quality=db.get_config("video_quality", app_settings.default_quality),
        max_concurrent_downloads=int(
            db.get_config("max_concurrent_downloads", str(app_settings.max_concurrent_downloads))
        ),
        auto_fetch_hls=db.get_config("auto_fetch_hls", "false").lower() == "true",
        is_logged_in=bool(db.get_config("pokergo_email")),
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(update: SettingsUpdate):
    """Update settings"""
    db = get_db()

    if update.pokergo_email is not None:
        db.set_config("pokergo_email", update.pokergo_email)

    if update.pokergo_password is not None:
        # In production, encrypt the password
        db.set_config("pokergo_password", update.pokergo_password)

    if update.download_path is not None:
        db.set_config("download_path", update.download_path)

    if update.video_quality is not None:
        db.set_config("video_quality", update.video_quality)

    if update.max_concurrent_downloads is not None:
        db.set_config("max_concurrent_downloads", str(update.max_concurrent_downloads))

    if update.auto_fetch_hls is not None:
        db.set_config("auto_fetch_hls", "true" if update.auto_fetch_hls else "false")

    return await get_settings()


@router.post("/test-login", response_model=LoginTestResponse)
async def test_login(request: LoginTestRequest):
    """Test PokerGO login credentials"""
    try:
        from ..services.hls_fetcher import test_login

        success = await test_login(request.email, request.password)

        if success:
            # Save credentials on successful login
            db = get_db()
            db.set_config("pokergo_email", request.email)
            db.set_config("pokergo_password", request.password)

            return LoginTestResponse(success=True, message="Login successful")
        else:
            return LoginTestResponse(success=False, message="Invalid credentials")

    except Exception as e:
        return LoginTestResponse(success=False, message=str(e))
