"""
PokerGO 비디오 다운로드 테스트
- m3u8 URL 추출 가능 여부 확인
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"


async def main():
    print("=" * 60)
    print("PokerGO Download Test")
    print("=" * 60)

    # 테스트할 비디오 URL 로드
    with open(DATA_DIR / "wsop_all_20251215_165040.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    test_videos = data["videos"][:3]  # 3개만 테스트

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    m3u8_urls = []

    # 네트워크 요청 캡처
    async def capture_m3u8(response):
        url = response.url
        if ".m3u8" in url or "manifest" in url.lower():
            m3u8_urls.append(url)
            print(f"  [M3U8] {url[:100]}")

    page.on("response", capture_m3u8)

    # Login
    print("\n[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("[SUCCESS] Login!")

    # 각 비디오 테스트
    for i, video in enumerate(test_videos):
        video_url = video["url"]
        print(f"\n[TEST {i+1}] {video_url}")

        m3u8_urls.clear()

        try:
            await page.goto(video_url, wait_until="networkidle")
            await page.wait_for_timeout(5000)

            # 재생 버튼 클릭 시도
            play_btn = await page.query_selector('[class*="play"], button[aria-label*="Play"]')
            if play_btn:
                await play_btn.click()
                await page.wait_for_timeout(3000)

            # 비디오 요소 확인
            video_el = await page.query_selector("video")
            if video_el:
                src = await video_el.get_attribute("src")
                print(f"  [VIDEO SRC] {src[:100] if src else 'None'}")

            # m3u8 URL 확인
            if m3u8_urls:
                print(f"  [RESULT] Found {len(m3u8_urls)} m3u8 URLs!")
                for url in m3u8_urls[:3]:
                    print(f"    - {url[:80]}...")
            else:
                print("  [RESULT] No m3u8 URL found")

                # HTML에서 직접 검색
                html = await page.content()
                if "m3u8" in html:
                    import re
                    found = re.findall(r'https?://[^\s"\']+\.m3u8[^\s"\']*', html)
                    if found:
                        print(f"  [HTML] Found {len(found)} m3u8 in HTML:")
                        for url in found[:3]:
                            print(f"    - {url[:80]}...")

        except Exception as e:
            print(f"  [ERROR] {str(e)[:50]}")

    await browser.close()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
