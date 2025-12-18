"""
WSOP 최종 스크래퍼 - collections 기반
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

WSOP_YEARS = ["2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017", "2016", "2015", "2014", "2013", "2012", "2011"]


async def main():
    print("=" * 60)
    print("WSOP Final Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = {}
    all_collections = {}
    year_counts = {}

    # Login
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("[SUCCESS] Login!\n")

    for year in WSOP_YEARS:
        url = f"https://www.pokergo.com/collections/wsop-{year}"
        print(f"\n{'='*60}")
        print(f"[YEAR] WSOP {year}")
        print("=" * 60)

        try:
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 하위 컬렉션 링크 찾기
            links = await page.evaluate('''() => {
                const result = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href || '';
                    const text = (a.innerText || '').trim();
                    if (href.includes('/collections/wsop-')) {
                        result.push({ href, text: text.substring(0, 100) });
                    }
                });
                return result;
            }''')

            # 중복 제거 및 현재 페이지 제외
            sub_collections = []
            seen = set()
            for link in links:
                if link['href'] not in seen and link['href'] != url:
                    seen.add(link['href'])
                    sub_collections.append(link)

            print(f"  Found {len(sub_collections)} sub-collections")
            for c in sub_collections:
                print(f"    - {c['text'][:50]}")

            # 각 하위 컬렉션 스크래핑
            for coll in sub_collections:
                coll_url = coll['href']
                coll_name = coll['text'] or coll_url.split('/')[-1]

                print(f"\n  [COLLECTION] {coll_name[:50]}")

                try:
                    await page.goto(coll_url, wait_until="networkidle")
                    await page.wait_for_timeout(3000)

                    # 스크롤
                    for _ in range(15):
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        await page.wait_for_timeout(800)

                    # 비디오 링크 추출
                    videos = await page.evaluate('''() => {
                        const videos = [];
                        document.querySelectorAll('a').forEach(a => {
                            const href = a.href || '';
                            if (href.includes('/videos/')) {
                                videos.push({
                                    url: href,
                                    title: (a.innerText || '').trim().substring(0, 150)
                                });
                            }
                        });
                        return videos;
                    }''')

                    # 중복 제거
                    unique_videos = {}
                    for v in videos:
                        if v['url'] not in unique_videos:
                            unique_videos[v['url']] = v

                    print(f"    Found {len(unique_videos)} videos")

                    all_collections[coll_url] = {
                        "url": coll_url,
                        "name": coll_name,
                        "year": year,
                        "video_count": len(unique_videos)
                    }

                    for v in unique_videos.values():
                        if v['url'] not in all_videos:
                            all_videos[v['url']] = {
                                **v,
                                "year": year,
                                "collection": coll_name
                            }

                except Exception as e:
                    print(f"    Error: {str(e)[:50]}")

            year_counts[year] = len([v for v in all_videos.values() if v.get('year') == year])

        except Exception as e:
            print(f"  Error: {str(e)[:50]}")
            year_counts[year] = 0

    await browser.close()

    # 결과 출력
    print(f"\n\n{'='*60}")
    print("WSOP Videos Summary:")
    print("=" * 60)
    for year in WSOP_YEARS:
        count = year_counts.get(year, 0)
        print(f"  {year}: {count} videos")
    print(f"\n  TOTAL: {len(all_videos)} unique videos")
    print(f"  Collections: {len(all_collections)}")

    # 저장
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total_videos": len(all_videos),
        "total_collections": len(all_collections),
        "by_year": year_counts,
        "collections": list(all_collections.values()),
        "videos": list(all_videos.values())
    }

    output_path = DATA_DIR / f"wsop_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nSaved to: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
