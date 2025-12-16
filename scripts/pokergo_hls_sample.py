"""
PokerGO HLS URL 샘플 추출 (처음 50개만)
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

SAMPLE_SIZE = 50  # 샘플 수


async def main():
    data_file = OUTPUT_DIR / "wsop_final_20251216_154021.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    videos = data.get("videos", [])[:SAMPLE_SIZE]
    print(f"Processing {len(videos)} sample videos")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    results = []

    try:
        # LOGIN
        print("\n[1/2] LOGIN")
        await page.goto("https://www.pokergo.com/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        await page.locator('input[placeholder="Email Address"]').fill(POKERGO_ID)
        await asyncio.sleep(0.5)
        await page.locator('input[placeholder="Password"]').fill(POKERGO_PASSWORD)
        await asyncio.sleep(0.5)
        await page.locator('button:has-text("Login")').click()
        await asyncio.sleep(5)

        if "login" not in page.url.lower():
            print("  [OK] Login successful!")
        else:
            print("  [ERROR] Login failed")
            return

        # EXTRACT HLS
        print("\n[2/2] EXTRACTING HLS URLs")

        for i, video in enumerate(videos):
            url = video.get("url", "")
            title = video.get("title", "")[:50]
            hls_url = ""

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # 비디오 재생 시도
                try:
                    play_btn = page.locator('[class*="play"], button[aria-label*="Play"]').first
                    await play_btn.click(timeout=3000)
                    await asyncio.sleep(3)
                except Exception:
                    pass

                # 페이지 소스에서 m3u8 찾기
                content = await page.content()
                m3u8_matches = re.findall(r'(https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)', content)

                if m3u8_matches:
                    # 가장 좋은 품질의 m3u8 선택 (보통 마스터 플레이리스트)
                    hls_url = m3u8_matches[0]
                    for m in m3u8_matches:
                        if 'master' in m.lower() or 'index' in m.lower():
                            hls_url = m
                            break

                status = "OK" if hls_url else "NO HLS"
                print(f"  [{i+1}/{len(videos)}] {status} - {title}")

            except Exception as e:
                print(f"  [{i+1}/{len(videos)}] ERROR - {title}: {str(e)[:30]}")

            results.append({
                "url": url,
                "title": video.get("title", ""),
                "year": video.get("year"),
                "category": video.get("category", ""),
                "hls_url": hls_url,
            })

            await asyncio.sleep(1)

        # SAVE
        found = sum(1 for r in results if r["hls_url"])
        print(f"\n[RESULT] HLS Found: {found}/{len(results)}")

        output_file = OUTPUT_DIR / f"wsop_hls_sample_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"Saved to: {output_file}")

        # 샘플 출력
        print("\n[SAMPLE HLS URLs]")
        for r in results[:10]:
            if r["hls_url"]:
                print(f"  {r['title'][:40]}")
                print(f"    {r['hls_url'][:80]}...")

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
