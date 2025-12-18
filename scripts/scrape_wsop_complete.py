"""
WSOP 완전 스크래퍼 - 모든 시리즈의 모든 비디오 수집
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
DATA_DIR.mkdir(parents=True, exist_ok=True)

WSOP_YEARS = [
    "2025", "2024", "2023", "2022", "2021", "2020",
    "2019", "2018", "2017", "2016", "2015", "2014",
    "2013", "2012", "2011"
]


async def main():
    print("=" * 60)
    print("WSOP Complete Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = {}
    all_series = {}
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
    for year in WSOP_YEARS:
        url = f"https://www.pokergo.com/collections/wsop-{year}"
        print(f"\n{'='*60}")
        print(f"[INFO] Scraping WSOP {year}...")
        print("=" * 60)

        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # HTML에서 시리즈 링크 추출
            html = await page.content()

            # /series/ 패턴 찾기
            series_urls = re.findall(r'href="(/series/[^"]+)"', html)
            series_urls = list(set(series_urls))

            print(f"  Found {len(series_urls)} series")

            # 각 시리즈 페이지 방문
            for series_url in series_urls:
                full_series_url = f"https://www.pokergo.com{series_url}"

                # 시리즈 이름 추출
                series_name = series_url.split('/')[-1].replace('-', ' ').title()
                print(f"\n  [SERIES] {series_name}")

                try:
                    await page.goto(full_series_url, wait_until="networkidle")
                    await page.wait_for_timeout(2000)

                    # 무한 스크롤
                    for _ in range(15):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(1000)

                    # HTML에서 비디오 URL 추출
                    series_html = await page.content()
                    video_urls = re.findall(r'href="(/videos/[^"]+)"', series_html)
                    video_urls = list(set(video_urls))

                    print(f"    Found {len(video_urls)} videos")

                    # 비디오 정보 저장
                    for video_url in video_urls:
                        full_video_url = f"https://www.pokergo.com{video_url}"
                        if full_video_url not in all_videos:
                            all_videos[full_video_url] = {
                                "url": full_video_url,
                                "year": year,
                                "series": series_name,
                                "video_id": video_url.split('/')[-1]
                            }

                    all_series[full_series_url] = {
                        "url": full_series_url,
                        "name": series_name,
                        "year": year,
                        "video_count": len(video_urls)
                    }

                except Exception as e:
                    print(f"    Error: {e}")

            year_counts[year] = len([v for v in all_videos.values() if v['year'] == year])
            print(f"\n  [TOTAL for {year}] {year_counts[year]} videos")

        except Exception as e:
            print(f"  Error: {e}")
            year_counts[year] = 0

    await browser.close()

    # 결과 출력
    print(f"\n{'='*60}")
    print("WSOP Videos Summary:")
    print("=" * 60)
    total = 0
    for year in WSOP_YEARS:
        count = year_counts.get(year, 0)
        print(f"  {year}: {count} videos")
        total += count
    print(f"\n  TOTAL: {len(all_videos)} unique videos")
    print(f"  Series: {len(all_series)}")

    # 저장
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total_videos": len(all_videos),
        "total_series": len(all_series),
        "by_year": year_counts,
        "series": list(all_series.values()),
        "videos": list(all_videos.values())
    }

    output_path = DATA_DIR / f"wsop_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
