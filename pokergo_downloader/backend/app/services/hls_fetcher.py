"""HLS URL Fetcher Service"""

import asyncio
from typing import List, Optional
from playwright.async_api import async_playwright

from .database import get_db
from ..config import settings


async def test_login(email: str, password: str) -> bool:
    """Test PokerGO login credentials"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
            await page.wait_for_timeout(2000)

            await page.fill('input[name="email"]', email)
            await page.fill('input[type="password"]', password)
            await page.click('button:has-text("Login")')
            await page.wait_for_timeout(5000)

            # Check if login successful
            current_url = page.url
            return "login" not in current_url.lower()

        except Exception as e:
            print(f"Login test error: {e}")
            return False
        finally:
            await browser.close()


class HLSFetcher:
    """Fetches HLS URLs from PokerGO"""

    def __init__(self):
        self.is_running = False
        self.current_video: Optional[str] = None
        self.progress = 0
        self.total = 0
        self.completed = 0
        self.failed = 0
        self._cancel_requested = False

    async def fetch_batch(self, video_ids: List[str]):
        """Fetch HLS URLs for a batch of videos"""
        if self.is_running:
            return

        self.is_running = True
        self.total = len(video_ids)
        self.completed = 0
        self.failed = 0
        self._cancel_requested = False

        db = get_db()
        email = db.get_config("pokergo_email")
        password = db.get_config("pokergo_password")

        if not email or not password:
            self.is_running = False
            return

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}
            )
            page = await context.new_page()

            try:
                # Login
                await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
                await page.wait_for_timeout(2000)

                await page.fill('input[name="email"]', email)
                await page.fill('input[type="password"]', password)
                await page.click('button:has-text("Login")')
                await page.wait_for_timeout(5000)

                if "login" in page.url.lower():
                    print("Login failed")
                    self.is_running = False
                    return

                # Process each video
                for i, video_id in enumerate(video_ids):
                    if self._cancel_requested:
                        break

                    self.current_video = video_id
                    self.progress = int((i / self.total) * 100)

                    video = db.get_video(video_id)
                    if not video:
                        self.failed += 1
                        continue

                    hls_url = await self._get_hls_url(page, video.url)

                    if hls_url:
                        video.hls_url = hls_url
                        db.update_video(video)
                        self.completed += 1
                    else:
                        self.failed += 1

                    await asyncio.sleep(1)

            except Exception as e:
                print(f"Fetch error: {e}")
            finally:
                await browser.close()
                self.is_running = False
                self.current_video = None

    async def _get_hls_url(self, page, video_url: str) -> Optional[str]:
        """Extract HLS URL from video page"""
        import re

        captured_urls = []

        async def capture_response(response):
            url = response.url
            if "jwplayer" in url.lower():
                captured_urls.append(url)

        try:
            page.on("response", capture_response)

            await page.goto(video_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Try to click play button
            try:
                play_btn = await page.query_selector(
                    '[class*="play"], button[aria-label*="Play"], .jw-icon-playback'
                )
                if play_btn:
                    await play_btn.click()
                    await page.wait_for_timeout(3000)
            except:
                pass

            # Check captured URLs for JWPlayer media ID
            for url in captured_urls:
                if "cdn.jwplayer.com" in url and ".m3u8" in url:
                    match = re.search(r'https://cdn\.jwplayer\.com/manifests/([A-Za-z0-9]+)', url)
                    if match:
                        return f"https://cdn.jwplayer.com/manifests/{match.group(1)}.m3u8"
                    return url

                if "cdn.jwplayer.com/v2/media/" in url:
                    match = re.search(r'/v2/media/([A-Za-z0-9]+)', url)
                    if match:
                        return f"https://cdn.jwplayer.com/manifests/{match.group(1)}.m3u8"

            # Check video source
            video_src = await page.evaluate('''() => {
                const video = document.querySelector('video');
                return video ? video.src : null;
            }''')

            if video_src and "cdn.jwplayer.com" in video_src:
                match = re.search(r'/videos/([A-Za-z0-9]+)', video_src)
                if match:
                    return f"https://cdn.jwplayer.com/manifests/{match.group(1)}.m3u8"

            # Search in HTML
            html = await page.content()
            patterns = [
                r'"mediaid"\s*:\s*"([A-Za-z0-9]+)"',
                r'mediaid=([A-Za-z0-9]+)',
                r'/manifests/([A-Za-z0-9]+)\.m3u8',
                r'/videos/([A-Za-z0-9]+)-',
            ]

            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    media_id = match.group(1)
                    return f"https://cdn.jwplayer.com/manifests/{media_id}.m3u8"

            return None

        except Exception as e:
            print(f"Error getting HLS URL: {e}")
            return None
        finally:
            try:
                page.remove_listener("response", capture_response)
            except:
                pass

    def cancel(self):
        """Cancel ongoing fetch"""
        self._cancel_requested = True


# Singleton instance
_fetcher_instance: Optional[HLSFetcher] = None


def get_hls_fetcher() -> HLSFetcher:
    """Get HLS fetcher instance"""
    global _fetcher_instance
    if _fetcher_instance is None:
        _fetcher_instance = HLSFetcher()
    return _fetcher_instance
