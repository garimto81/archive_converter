"""
WSOP 연도별 비디오 스크래퍼
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

# WSOP 연도별 컬렉션 URL
WSOP_YEARS = [
    ("2025", "https://www.pokergo.com/collections/wsop-2025"),
    ("2024", "https://www.pokergo.com/collections/wsop-2024"),
    ("2023", "https://www.pokergo.com/collections/wsop-2023"),
    ("2022", "https://www.pokergo.com/collections/wsop-2022"),
    ("2021", "https://www.pokergo.com/collections/wsop-2021"),
    ("2020", "https://www.pokergo.com/collections/wsop-2020"),
    ("2019", "https://www.pokergo.com/collections/wsop-2019"),
    ("2018", "https://www.pokergo.com/collections/wsop-2018"),
    ("2017", "https://www.pokergo.com/collections/wsop-2017"),
    ("2016", "https://www.pokergo.com/collections/wsop-2016"),
    ("2015", "https://www.pokergo.com/collections/wsop-2015"),
    ("2014", "https://www.pokergo.com/collections/wsop-2014"),
    ("2013", "https://www.pokergo.com/collections/wsop-2013"),
    ("2012", "https://www.pokergo.com/collections/wsop-2012"),
    ("2011", "https://www.pokergo.com/collections/wsop-2011"),
]


async def main():
    print("=" * 60)
    print("WSOP Years Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = {}
    year_counts = {}

    # Login
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)

    if "login" not in page.url.lower():
        print("[SUCCESS] Login successful!\n")
    else:
        print("[ERROR] Login failed!")
        await browser.close()
        return

    # 각 연도별 페이지 스크래핑
    for year, url in WSOP_YEARS:
        print(f"\n[INFO] Scraping WSOP {year}...")
        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 스크린샷
            await page.screenshot(path=str(DATA_DIR / f"wsop_{year}.png"))

            # 스크롤하여 모든 콘텐츠 로드
            last_height = 0
            for i in range(20):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1500)

                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # innerHTML에서 비디오 URL 직접 추출
            html = await page.content()

            # /videos/ 패턴 찾기
            import re
            video_urls = re.findall(r'href="(/videos/[^"]+)"', html)
            video_urls = list(set(video_urls))  # 중복 제거

            print(f"  Found {len(video_urls)} video URLs in HTML")

            # 각 비디오 정보 저장
            for video_url in video_urls:
                full_url = f"https://www.pokergo.com{video_url}"
                if full_url not in all_videos:
                    all_videos[full_url] = {
                        "url": full_url,
                        "year": year,
                        "title": ""  # 나중에 채움
                    }

            year_counts[year] = len(video_urls)

        except Exception as e:
            print(f"  Error: {e}")
            year_counts[year] = 0

    await browser.close()

    # 결과 출력
    print(f"\n{'='*60}")
    print("WSOP Videos by Year:")
    print("=" * 60)
    total = 0
    for year, count in sorted(year_counts.items(), reverse=True):
        print(f"  {year}: {count} videos")
        total += count
    print(f"\n  Total: {total} videos (unique: {len(all_videos)})")

    # 저장
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(all_videos),
        "by_year": year_counts,
        "videos": list(all_videos.values())
    }

    output_path = DATA_DIR / f"wsop_all_years_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
