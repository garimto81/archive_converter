"""
WSOP Collection 페이지 스크래퍼 - 시즌별 비디오 수집
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
    print("WSOP Collection Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    all_videos = []
    api_responses = []

    # API 응답 캡처
    async def capture_response(response):
        url = response.url
        if response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    api_responses.append({"url": url, "data": data})
                    print(f"  [API] {url[:80]}")
            except Exception:
                pass

    page.on("response", capture_response)

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

    # WSOP Collection 페이지로 이동
    print("[INFO] Going to WSOP Collection page...")
    await page.goto("https://www.pokergo.com/collections/world-series-of-poker", wait_until="networkidle")
    await page.wait_for_timeout(5000)

    # Screenshot
    await page.screenshot(path=str(DATA_DIR / "wsop_collection.png"), full_page=True)
    print("[INFO] Screenshot saved: wsop_collection.png")

    # 전체 HTML 저장
    html_content = await page.content()
    with open(DATA_DIR / "wsop_collection.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    print("[INFO] HTML saved: wsop_collection.html")

    # 시즌/시리즈 링크 찾기
    print("\n[INFO] Looking for seasons/series links...")
    seasons = await page.evaluate('''() => {
        const seasons = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.href || '';
            const text = a.textContent?.trim() || '';
            if (href.includes('/series/') || href.includes('/seasons/') ||
                text.match(/season|20[0-9]{2}|wsop/i)) {
                seasons.push({href, text: text.substring(0, 100)});
            }
        });
        return seasons;
    }''')

    print(f"  Found {len(seasons)} potential season links:")
    for s in seasons[:20]:
        print(f"    - {s['text'][:50]}: {s['href'][:60]}")

    # 무한 스크롤 시도
    print("\n[INFO] Scrolling to load more content...")
    for i in range(30):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1500)
        if i % 5 == 0:
            print(f"  Scroll {i+1}/30...")

    # 스크롤 후 스크린샷
    await page.screenshot(path=str(DATA_DIR / "wsop_collection_scrolled.png"), full_page=True)

    # 모든 링크 분석
    print("\n[INFO] Analyzing all links after scrolling...")
    all_links = await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.href || a.getAttribute('href') || '';
            links.push({
                href: href,
                text: a.textContent?.trim()?.substring(0, 100) || '',
                classes: a.className || ''
            });
        });
        return links;
    }''')

    # 비디오 링크 필터링
    video_links = [lnk for lnk in all_links if '/videos/' in lnk.get('href', '') or '/watch/' in lnk.get('href', '')]
    print(f"\n[VIDEO LINKS] Found {len(video_links)}")
    for v in video_links[:10]:
        print(f"  - {v['href']}")

    # 시리즈/시즌 링크
    series_links = [lnk for lnk in all_links if '/series/' in lnk.get('href', '')]
    print(f"\n[SERIES LINKS] Found {len(series_links)}")
    for s in series_links[:20]:
        print(f"  - {s['text'][:40]}: {s['href']}")

    # 시리즈 페이지 탐색
    visited_series = set()
    for series in series_links:
        series_url = series['href']
        if series_url in visited_series:
            continue
        visited_series.add(series_url)

        print(f"\n[INFO] Exploring series: {series['text'][:40]}...")
        try:
            await page.goto(series_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # 스크롤
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)

            # 비디오 링크 추출
            videos = await page.evaluate('''() => {
                const videos = [];
                document.querySelectorAll('a').forEach(a => {
                    const href = a.href || a.getAttribute('href') || '';
                    if (href.includes('/videos/')) {
                        videos.push({
                            url: href,
                            title: a.textContent?.trim()?.substring(0, 150) || ''
                        });
                    }
                });
                return videos;
            }''')

            print(f"  Found {len(videos)} videos")
            for v in videos:
                v['series'] = series['text']
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

    # Save results
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(unique),
        "videos": list(unique.values())
    }

    output_path = DATA_DIR / f"wsop_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Save API responses
    api_path = DATA_DIR / f"wsop_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(api_path, "w", encoding="utf-8") as f:
        json.dump(api_responses, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Found {len(unique)} unique WSOP videos!")
    print(f"Saved to: {output_path}")
    print(f"API responses: {api_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
