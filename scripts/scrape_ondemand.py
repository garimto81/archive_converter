"""
PokerGO On Demand 페이지 스크래퍼 - 전체 비디오 수집
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
    print("PokerGO On Demand Scraper")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    _all_videos = []  # reserved for future use
    api_responses = []

    # API 응답 캡처
    async def capture_response(response):
        url = response.url
        if "api.pokergo.com" in url and response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    api_responses.append({"url": url, "data": data})
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
        print("[SUCCESS] Login successful!")
    else:
        print("[ERROR] Login failed!")
        await browser.close()
        return

    # On Demand 페이지로 이동
    print("\n[INFO] Going to On Demand page...")
    await page.goto("https://www.pokergo.com/on-demand", wait_until="networkidle")
    await page.wait_for_timeout(5000)

    # Screenshot
    await page.screenshot(path=str(DATA_DIR / "ondemand_page.png"), full_page=True)
    print("[INFO] Screenshot saved")

    # Scroll and collect
    print("\n[INFO] Scrolling to load all content...")
    last_count = 0
    scroll_count = 0
    max_scrolls = 50

    while scroll_count < max_scrolls:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)

        # Count current links
        current_links = await page.evaluate('''() => {
            return document.querySelectorAll('a[href*="/videos/"], a[href*="/watch/"]').length;
        }''')

        if current_links == last_count:
            scroll_count += 1
            if scroll_count >= 3:  # 3번 연속 변화 없으면 종료
                break
        else:
            scroll_count = 0
            last_count = current_links
            print(f"  Found {current_links} video links so far...")

    # Extract all video links
    print("\n[INFO] Extracting video information...")
    videos = await page.evaluate('''() => {
        const videos = [];
        const seen = new Set();

        document.querySelectorAll('a').forEach(el => {
            const href = el.getAttribute('href') || '';
            if ((href.includes('/videos/') || href.includes('/watch/')) && !seen.has(href)) {
                seen.add(href);

                // Try to find title and thumbnail
                const container = el.closest('[class*="card"], [class*="item"], [class*="tile"]') || el;
                const title = container.querySelector('h1, h2, h3, h4, [class*="title"]')?.textContent?.trim() ||
                             el.getAttribute('title') ||
                             el.textContent?.trim()?.substring(0, 150) || '';
                const img = container.querySelector('img')?.src ||
                           el.querySelector('img')?.src || '';

                videos.push({
                    url: href.startsWith('http') ? href : 'https://www.pokergo.com' + href,
                    title: title.replace(/\\s+/g, ' ').trim(),
                    thumbnail: img
                });
            }
        });

        return videos;
    }''')

    print(f"\n[INFO] Found {len(videos)} videos from On Demand page")

    # 추가 페이지 탐색
    nav_links = await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.href || '';
            const text = a.textContent?.trim() || '';
            if (href && (
                text.toLowerCase().includes('wsop') ||
                text.toLowerCase().includes('world series') ||
                href.includes('/shows/') ||
                href.includes('/collections/')
            )) {
                links.push({href, text});
            }
        });
        return links;
    }''')

    print(f"\n[INFO] Found {len(nav_links)} additional navigation links")
    for link in nav_links[:10]:
        print(f"  - {link['text']}: {link['href']}")

    # WSOP 관련 링크 탐색
    wsop_pages = []
    for link in nav_links:
        if 'wsop' in link['href'].lower() or 'world series' in link['text'].lower():
            wsop_pages.append(link['href'])

    for wsop_url in wsop_pages[:5]:
        print(f"\n[INFO] Exploring: {wsop_url}")
        try:
            await page.goto(wsop_url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Scroll
            for _ in range(10):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)

            more_videos = await page.evaluate('''() => {
                const videos = [];
                document.querySelectorAll('a[href*="/videos/"]').forEach(el => {
                    const href = el.getAttribute('href');
                    if (href) {
                        videos.push({
                            url: href.startsWith('http') ? href : 'https://www.pokergo.com' + href,
                            title: el.textContent?.trim()?.substring(0, 150) || '',
                            thumbnail: el.querySelector('img')?.src || ''
                        });
                    }
                });
                return videos;
            }''')

            print(f"  Found {len(more_videos)} videos")
            videos.extend(more_videos)

        except Exception as e:
            print(f"  Error: {e}")

    await browser.close()

    # Deduplicate
    unique = {}
    for v in videos:
        url = v.get('url', '')
        if url and url not in unique:
            unique[url] = v

    # Filter WSOP
    wsop_videos = {url: v for url, v in unique.items() if 'wsop' in url.lower()}

    # Save
    output = {
        "scraped_at": datetime.now().isoformat(),
        "total": len(unique),
        "wsop_count": len(wsop_videos),
        "videos": list(unique.values()),
        "wsop_videos": list(wsop_videos.values())
    }

    output_path = DATA_DIR / f"pokergo_ondemand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # Save API responses
    api_path = DATA_DIR / f"pokergo_api_ondemand_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(api_path, "w", encoding="utf-8") as f:
        json.dump(api_responses, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] Scraped {len(unique)} unique videos!")
    print(f"  - WSOP: {len(wsop_videos)}")
    print(f"  - Other: {len(unique) - len(wsop_videos)}")
    print(f"\nSaved to: {output_path}")
    print(f"API responses: {api_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
