"""
WSOP 시즌별 비디오 스크래퍼
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    print("=" * 60)
    print("WSOP Seasons Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = []

    # Login
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)

    if "login" not in page.url.lower():
        print("[SUCCESS] Login successful!")
    else:
        print("[ERROR] Login failed!")
        await browser.close()
        return

    # WSOP 관련 페이지들
    wsop_pages = [
        "/wsop",
        "/shows/wsop-main-event",
        "/shows/wsop-bracelet-events",
        "/shows/world-series-of-poker",
        "/shows/wsop-2024",
        "/shows/wsop-2023",
        "/shows/wsop-2022",
        "/shows/wsop-2021",
        "/shows/wsop-2020",
        "/shows/wsop-2019",
        "/shows/wsop-2018",
        "/shows/wsop-2017",
        "/shows/wsop-2016",
        "/shows/wsop-2015",
    ]

    for path in wsop_pages:
        print(f"\n[INFO] Scraping: {path}")
        try:
            await page.goto(f"https://www.pokergo.com{path}", wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Scroll to load more content
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)

            # Extract video links
            videos = await page.evaluate('''() => {
                const videos = [];
                document.querySelectorAll('a[href*="/videos/"]').forEach(el => {
                    const href = el.getAttribute("href");
                    const title = el.querySelector("[class*='title'], h2, h3, h4")?.textContent?.trim() ||
                                 el.textContent?.trim()?.substring(0, 150) || "";
                    const img = el.querySelector("img")?.src;

                    if (href && !videos.find(v => v.url === href)) {
                        videos.push({
                            url: href.startsWith("http") ? href : "https://www.pokergo.com" + href,
                            title: title.replace(/\\s+/g, ' ').trim(),
                            thumbnail: img
                        });
                    }
                });
                return videos;
            }''')

            print(f"  Found {len(videos)} videos")
            for v in videos:
                v['source'] = path
            all_videos.extend(videos)

        except Exception as e:
            print(f"  Error: {e}")

    await browser.close()

    # Deduplicate
    unique = {}
    for v in all_videos:
        url = v.get('url', '')
        if url and url not in unique:
            unique[url] = v

    # Save
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(unique),
        "videos": list(unique.values())
    }

    output_path = DATA_DIR / f"wsop_seasons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Scraped {len(unique)} unique WSOP videos!")
    print(f"Saved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
