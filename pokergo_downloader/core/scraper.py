"""PokerGO Scraper - Login and HLS URL extraction"""

import re
import asyncio
from typing import Optional, List, Dict, Callable
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class PokerGOScraper:
    """Scraper for PokerGO video HLS URLs"""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False

    async def start(self, headless: bool = True):
        """Start browser"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await self.context.new_page()

    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.context = None
            self.page = None
            self.is_logged_in = False

    async def login(self) -> bool:
        """Login to PokerGO"""
        if not self.page:
            return False

        try:
            await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)

            # Fill credentials
            await self.page.fill('input[name="email"]', self.email)
            await self.page.fill('input[type="password"]', self.password)

            # Click login button
            await self.page.click('button:has-text("Login")')
            await self.page.wait_for_timeout(5000)

            # Check if login successful by checking URL redirect
            current_url = self.page.url
            self.is_logged_in = "login" not in current_url.lower()

            return self.is_logged_in

        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def get_hls_url(self, video_url: str) -> Optional[str]:
        """Get HLS URL from video page"""
        if not self.page or not self.is_logged_in:
            return None

        captured_urls = []

        async def capture_response(response):
            url = response.url
            if "jwplayer" in url.lower():
                captured_urls.append(url)

        try:
            # Listen for network requests
            self.page.on("response", capture_response)

            await self.page.goto(video_url, wait_until="networkidle")
            await self.page.wait_for_timeout(3000)

            # Try to click play button
            try:
                play_btn = await self.page.query_selector('[class*="play"], button[aria-label*="Play"], .jw-icon-playback')
                if play_btn:
                    await play_btn.click()
                    await self.page.wait_for_timeout(3000)
            except Exception:
                pass

            # Method 1: Check captured URLs for JWPlayer media ID
            for url in captured_urls:
                # Direct manifest URL
                if "cdn.jwplayer.com" in url and ".m3u8" in url:
                    match = re.search(r'https://cdn\.jwplayer\.com/manifests/([A-Za-z0-9]+)', url)
                    if match:
                        return f"https://cdn.jwplayer.com/manifests/{match.group(1)}.m3u8"
                    return url

                # Media API URL (e.g., cdn.jwplayer.com/v2/media/tM2d76So)
                if "cdn.jwplayer.com/v2/media/" in url:
                    match = re.search(r'/v2/media/([A-Za-z0-9]+)', url)
                    if match:
                        return f"https://cdn.jwplayer.com/manifests/{match.group(1)}.m3u8"

            # Method 2: Get video source from DOM
            video_src = await self.page.evaluate('''() => {
                const video = document.querySelector('video');
                return video ? video.src : null;
            }''')

            if video_src and "cdn.jwplayer.com" in video_src:
                match = re.search(r'/videos/([A-Za-z0-9]+)', video_src)
                if match:
                    jwplayer_id = match.group(1)
                    return f"https://cdn.jwplayer.com/manifests/{jwplayer_id}.m3u8"

            # Method 3: Search in page HTML
            html = await self.page.content()

            # Look for JWPlayer media ID in HTML
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
            print(f"Error getting HLS URL for {video_url}: {e}")
            return None
        finally:
            # Remove listener
            try:
                self.page.remove_listener("response", capture_response)
            except Exception:
                pass

    async def batch_get_hls_urls(
        self,
        video_urls: List[str],
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, str]:
        """Get HLS URLs for multiple videos"""
        results = {}
        total = len(video_urls)

        for i, url in enumerate(video_urls):
            hls_url = await self.get_hls_url(url)
            if hls_url:
                results[url] = hls_url

            if progress_callback:
                progress_callback(i + 1, total, url)

            # Small delay between requests
            await asyncio.sleep(1)

        return results


def run_scraper_sync(
    email: str,
    password: str,
    video_urls: List[str],
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    headless: bool = True
) -> Dict[str, str]:
    """Synchronous wrapper for scraper"""

    async def _run():
        scraper = PokerGOScraper(email, password)
        try:
            await scraper.start(headless=headless)
            if await scraper.login():
                return await scraper.batch_get_hls_urls(video_urls, progress_callback)
            return {}
        finally:
            await scraper.close()

    return asyncio.run(_run())
