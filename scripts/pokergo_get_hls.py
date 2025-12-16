"""
PokerGO HLS URL 추출

각 비디오 페이지에서 m3u8 스트리밍 URL 추출
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"


async def main():
    # 최종 데이터 로드
    data_file = OUTPUT_DIR / "wsop_final_20251216_154021.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])
    print(f"Total videos to process: {len(videos)}")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    # HLS URL 캡처를 위한 네트워크 리스너
    hls_urls = {}

    async def handle_response(response):
        url = response.url
        if '.m3u8' in url or 'manifest' in url.lower():
            # 현재 비디오 URL에 대한 HLS URL 저장
            if hasattr(page, '_current_video_url'):
                hls_urls[page._current_video_url] = url

    page.on("response", handle_response)

    try:
        # === LOGIN ===
        print("\n[1/3] LOGIN")
        await page.goto("https://www.pokergo.com/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        email_input = page.locator('input[placeholder="Email Address"]')
        pwd_input = page.locator('input[placeholder="Password"]')
        login_btn = page.locator('button:has-text("Login")')

        await email_input.fill(POKERGO_ID)
        await asyncio.sleep(0.5)
        await pwd_input.fill(POKERGO_PASSWORD)
        await asyncio.sleep(0.5)
        await login_btn.click()
        await asyncio.sleep(5)

        if "login" not in page.url.lower():
            print("  [OK] Login successful!")
        else:
            print("  [ERROR] Login failed")
            return

        # === GET HLS URLs ===
        print("\n[2/3] EXTRACTING HLS URLs")

        processed = 0
        found_hls = 0

        for i, video in enumerate(videos):
            url = video.get("url", "")
            if not url:
                continue

            processed += 1
            page._current_video_url = url

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")

                # 비디오 플레이어 찾기 및 재생 시도
                play_btn = page.locator('button[aria-label*="Play"], [class*="play"], video')
                try:
                    await play_btn.first.click(timeout=3000)
                except Exception:
                    pass

                await asyncio.sleep(3)

                # 페이지 소스에서 m3u8 URL 찾기
                content = await page.content()
                m3u8_match = re.search(r'(https?://[^"\']+\.m3u8[^"\']*)', content)

                if m3u8_match:
                    video["hls_url"] = m3u8_match.group(1)
                    found_hls += 1
                elif url in hls_urls:
                    video["hls_url"] = hls_urls[url]
                    found_hls += 1
                else:
                    video["hls_url"] = ""

                if processed % 10 == 0:
                    print(f"  Processed: {processed}/{len(videos)} (HLS found: {found_hls})")

            except Exception:
                video["hls_url"] = ""
                if processed % 10 == 0:
                    print(f"  Processed: {processed}/{len(videos)} (HLS found: {found_hls})")

            # 너무 빠른 요청 방지
            await asyncio.sleep(1)

            # 100개마다 중간 저장
            if processed % 100 == 0:
                temp_file = OUTPUT_DIR / f"wsop_with_hls_temp_{processed}.json"
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump({"videos": videos[:processed]}, f, ensure_ascii=False, indent=2)
                print(f"  [SAVE] Temp saved: {temp_file}")

        # === SAVE ===
        print("\n[3/3] SAVING DATA")

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(videos),
            "hls_found": found_hls,
            "videos": videos,
        }

        output_file = OUTPUT_DIR / f"wsop_with_hls_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[RESULT]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print(f"  Total: {len(videos)}")
        print(f"  HLS Found: {found_hls} ({found_hls/len(videos)*100:.1f}%)")

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
