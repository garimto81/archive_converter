"""
WSOP 스크래퍼 - DOM에서 직접 추출
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

WSOP_YEARS = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015"]


async def main():
    print("=" * 60)
    print("WSOP DOM Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = {}
    all_series = {}

    # Login
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("[SUCCESS] Login successful!\n")

    # 각 연도별 페이지
    for year in WSOP_YEARS:
        url = f"https://www.pokergo.com/collections/wsop-{year}"
        print(f"\n[YEAR] WSOP {year}")
        print("-" * 40)

        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # DOM에서 모든 링크 추출 (JavaScript 실행 후)
        links = await page.evaluate('''() => {
            const results = [];
            const allLinks = document.querySelectorAll('a');

            allLinks.forEach(a => {
                const href = a.href || '';
                const text = a.innerText?.trim() || '';

                if (href.includes('/series/') || href.includes('/videos/')) {
                    results.push({
                        href: href,
                        text: text.substring(0, 100),
                        type: href.includes('/series/') ? 'series' : 'video'
                    });
                }
            });

            return results;
        }''')

        series_links = [lnk for lnk in links if lnk['type'] == 'series']
        video_links = [lnk for lnk in links if lnk['type'] == 'video']

        print(f"  Series: {len(series_links)}, Videos: {len(video_links)}")

        # 시리즈 링크 탐색
        for series in series_links:
            series_url = series['href']
            series_name = series['text'] or series_url.split('/')[-1]

            if series_url in all_series:
                continue

            print(f"\n  [SERIES] {series_name[:50]}")

            try:
                await page.goto(series_url, wait_until="networkidle")
                await page.wait_for_timeout(3000)

                # 스크롤하여 더 많은 콘텐츠 로드
                for _ in range(10):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1000)

                # 비디오 링크 추출
                videos = await page.evaluate('''() => {
                    const videos = [];
                    document.querySelectorAll('a').forEach(a => {
                        const href = a.href || '';
                        if (href.includes('/videos/')) {
                            const text = a.innerText?.trim() || '';
                            const img = a.querySelector('img');
                            videos.push({
                                url: href,
                                title: text.substring(0, 150),
                                thumbnail: img ? img.src : ''
                            });
                        }
                    });
                    return videos;
                }''')

                print(f"    Found {len(videos)} videos")

                all_series[series_url] = {
                    "url": series_url,
                    "name": series_name,
                    "year": year,
                    "video_count": len(videos)
                }

                for v in videos:
                    if v['url'] not in all_videos:
                        all_videos[v['url']] = {
                            **v,
                            "year": year,
                            "series": series_name
                        }

            except Exception as e:
                print(f"    Error: {e}")

        # 연도 페이지의 직접 비디오도 추가
        for v in video_links:
            if v['href'] not in all_videos:
                all_videos[v['href']] = {
                    "url": v['href'],
                    "title": v['text'],
                    "year": year,
                    "series": "direct"
                }

    await browser.close()

    # 결과 출력
    print(f"\n{'='*60}")
    print("Results:")
    print("=" * 60)
    print(f"  Total videos: {len(all_videos)}")
    print(f"  Total series: {len(all_series)}")

    # 연도별 통계
    year_counts = {}
    for v in all_videos.values():
        y = v.get('year', 'unknown')
        year_counts[y] = year_counts.get(y, 0) + 1

    print("\nBy year:")
    for y in sorted(year_counts.keys(), reverse=True):
        print(f"  {y}: {year_counts[y]} videos")

    # 저장
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total_videos": len(all_videos),
        "total_series": len(all_series),
        "by_year": year_counts,
        "series": list(all_series.values()),
        "videos": list(all_videos.values())
    }

    output_path = DATA_DIR / f"wsop_dom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
