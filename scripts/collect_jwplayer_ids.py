"""
JWPlayer ID 수집 - 모든 WSOP 비디오
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

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"


async def main():
    print("=" * 60)
    print("JWPlayer ID Collector")
    print("=" * 60)

    # 비디오 목록 로드
    with open(DATA_DIR / "wsop_all_20251215_165040.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data["videos"]
    print(f"Total videos to process: {len(videos)}")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    results = []
    failed = []

    # Login
    print("\n[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("[SUCCESS] Login!\n")

    # 각 비디오 처리
    for i, video in enumerate(videos):
        video_url = video["url"]
        video_id = video_url.split("/")[-1]

        try:
            await page.goto(video_url, wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # video src에서 JWPlayer ID 추출
            video_src = await page.evaluate('''() => {
                const video = document.querySelector('video');
                return video ? video.src : null;
            }''')

            jwplayer_id = None
            if video_src and "cdn.jwplayer.com" in video_src:
                # https://cdn.jwplayer.com/videos/N8tOJB3q-sc8uFhWQ.mp4
                match = re.search(r'/videos/([A-Za-z0-9]+)', video_src)
                if match:
                    jwplayer_id = match.group(1)

            if jwplayer_id:
                result = {
                    "video_url": video_url,
                    "video_id": video_id,
                    "jwplayer_id": jwplayer_id,
                    "manifest_url": f"https://cdn.jwplayer.com/manifests/{jwplayer_id}.m3u8",
                    "title": video.get("title", ""),
                    "year": video.get("year", ""),
                }
                results.append(result)
                print(f"[{i+1}/{len(videos)}] {video_id}: {jwplayer_id}")
            else:
                failed.append({"url": video_url, "reason": "No JWPlayer ID found"})
                print(f"[{i+1}/{len(videos)}] {video_id}: FAILED")

        except Exception as e:
            failed.append({"url": video_url, "reason": str(e)[:50]})
            print(f"[{i+1}/{len(videos)}] {video_id}: ERROR - {str(e)[:30]}")

        # 중간 저장 (50개마다)
        if (i + 1) % 50 == 0:
            temp_output = {
                "scraped_at": datetime.now().isoformat(),
                "processed": i + 1,
                "success": len(results),
                "failed": len(failed),
                "videos": results
            }
            with open(DATA_DIR / "wsop_jwplayer_temp.json", "w", encoding="utf-8") as f:
                json.dump(temp_output, f, ensure_ascii=False, indent=2)
            print(f"\n  [SAVED] {len(results)} videos so far\n")

    await browser.close()

    # 최종 저장
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total_processed": len(videos),
        "success_count": len(results),
        "failed_count": len(failed),
        "videos": results,
        "failed": failed
    }

    output_path = DATA_DIR / f"wsop_jwplayer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print("Collection Complete!")
    print(f"  Success: {len(results)}/{len(videos)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
