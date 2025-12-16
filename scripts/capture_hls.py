# -*- coding: utf-8 -*-
"""
PokerGO HLS 스트림 캡처 및 다운로드
"""
import asyncio
import os
import sys
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(Path(__file__).parent.parent / ".env")
POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo" / "downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class HLSCapture:
    def __init__(self):
        self.hls_urls = []
        self.all_requests = []

    async def capture_request(self, request):
        url = request.url
        if ".m3u8" in url:
            self.hls_urls.append(url)
            print(f"  [HLS REQ] {url[:100]}...")
        elif "manifest" in url.lower() or "stream" in url.lower() or "media" in url.lower():
            self.all_requests.append(url)

    async def capture_response(self, response):
        url = response.url
        if ".m3u8" in url or "manifest" in url.lower():
            if url not in self.hls_urls:
                self.hls_urls.append(url)
                print(f"  [HLS RESP] {url[:100]}...")


async def main():
    # 발견된 비디오 ID
    video_id = "422cf804-6fd8-4e41-a5fb-29fe1e5a4ef7"
    video_url = f"https://www.pokergo.com/videos/{video_id}"

    capture = HLSCapture()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    page.on("request", capture.capture_request)
    page.on("response", capture.capture_response)

    # 로그인
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)

    await page.fill('input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("Login")')
    await page.wait_for_timeout(5000)

    if "login" not in page.url.lower():
        print("[OK] Login successful!")
    else:
        print("[WARN] Login may have failed")
        await browser.close()
        await playwright.stop()
        return

    # 비디오 페이지 방문
    print(f"\n[INFO] Opening video: {video_url}")
    await page.goto(video_url, wait_until="networkidle")
    await page.wait_for_timeout(5000)

    # 페이지 확인
    title = await page.title()
    print(f"[INFO] Page title: {title}")

    # 비디오 플레이어 확인
    video_info = await page.evaluate("""() => {
        const video = document.querySelector('video');
        const player = document.querySelector('[class*="player"], [id*="player"]');
        return {
            hasVideo: !!video,
            videoSrc: video ? video.src : null,
            hasPlayer: !!player
        };
    }""")
    print(f"[INFO] Video element: {video_info}")

    # JWPlayer 재생 버튼 먼저 클릭
    try:
        # JWPlayer 재생 버튼
        play_btn = await page.query_selector('div[aria-label="Play"]')
        if play_btn:
            print("  [INFO] Found JWPlayer play button, clicking...")
            await play_btn.click(force=True)
            print("  [INFO] Waiting for video to load (10s)...")
            await page.wait_for_timeout(10000)
        else:
            print("  [INFO] No JWPlayer button found, trying keyboard...")
            # 플레이어 영역 클릭 후 Space
            player = await page.query_selector('[class*="jw-"]')
            if player:
                await player.click(force=True)
                await page.wait_for_timeout(1000)
            await page.keyboard.press("Space")
            await page.wait_for_timeout(10000)
    except Exception as e:
        print(f"  [INFO] Play click error: {e}")

    # Space 키로 재생 시도
    try:
        await page.keyboard.press("Space")
        await page.wait_for_timeout(3000)
    except Exception:
        pass

    # 결과 확인
    print(f"\n[RESULT] HLS URLs captured: {len(capture.hls_urls)}")
    for url in capture.hls_urls:
        print(f"  {url}")

    # HLS URL이 있으면 다운로드 시도
    if capture.hls_urls:
        m3u8_url = capture.hls_urls[0]
        output_file = OUTPUT_DIR / "test_video.mp4"

        print("\n[INFO] Downloading HLS stream...")
        print(f"  URL: {m3u8_url[:100]}...")

        cmd = [
            "yt-dlp",
            "--no-check-certificate",
            "-o", str(output_file),
            m3u8_url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            print(f"[STDOUT] {result.stdout[:500] if result.stdout else 'None'}")
            print(f"[STDERR] {result.stderr[:500] if result.stderr else 'None'}")

            if result.returncode == 0 and output_file.exists():
                print(f"[OK] Downloaded: {output_file}")
                print(f"  Size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")
        except subprocess.TimeoutExpired:
            print("[WARN] Download timeout (60s)")
        except Exception as e:
            print(f"[ERROR] {e}")
    else:
        print("\n[WARN] No HLS URLs captured")

        # 스크린샷 저장
        await page.screenshot(path=str(OUTPUT_DIR / "no_hls_page.png"))
        print("[INFO] Screenshot saved: no_hls_page.png")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
