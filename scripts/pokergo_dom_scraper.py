"""
PokerGO DOM-based Scraper

웹페이지 DOM에서 직접 비디오 데이터 추출
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

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class DOMScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.all_videos = []

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,
            slow_mo=100  # Slow down to see what's happening
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        print("[INFO] Browser started")

    async def login_interactive(self, timeout_seconds=120):
        """Interactive login with auto-click attempt"""
        print("\n" + "=" * 60)
        print("AUTOMATIC LOGIN ATTEMPT")
        print("=" * 60)

        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # Screenshot for debugging
        await self.page.screenshot(path=str(OUTPUT_DIR / "login_page.png"))
        print("[DEBUG] Login page screenshot saved")

        # Try multiple login approaches
        try:
            # Approach 1: Standard form
            email = await self.page.query_selector('input[type="email"], input[name="email"], input[placeholder*="Email"]')
            if email:
                await email.click()
                await email.fill(POKERGO_ID)
                await self.page.wait_for_timeout(500)
                print(f"[OK] Email filled: {POKERGO_ID}")

            pwd = await self.page.query_selector('input[type="password"]')
            if pwd:
                await pwd.click()
                await pwd.fill(POKERGO_PASSWORD)
                await self.page.wait_for_timeout(500)
                print("[OK] Password filled")

            # Try to find and click login button
            btn_selectors = [
                'button[type="submit"]',
                'button:has-text("Log In")',
                'button:has-text("LOGIN")',
                'button:has-text("Sign In")',
                'input[type="submit"]',
                '[data-testid="login-button"]',
                '.login-button',
                '#login-button',
            ]

            for selector in btn_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        print(f"[INFO] Found login button: {selector}")
                        await btn.click()
                        await self.page.wait_for_timeout(5000)
                        break
                except Exception:
                    continue

            # Check if login succeeded
            if "login" not in self.page.url.lower():
                print("[OK] Login successful!")
                return True

            # Approach 2: Press Enter
            print("[INFO] Trying Enter key...")
            await self.page.keyboard.press("Enter")
            await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url.lower():
                print("[OK] Login successful!")
                return True

        except Exception as e:
            print(f"[ERROR] Auto-login failed: {e}")

        # Fallback: Wait for manual login
        print("\n[INFO] Auto-login may have failed. Waiting for manual login...")
        print(f"  Please log in within {timeout_seconds} seconds")

        start = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start) < timeout_seconds:
            await self.page.wait_for_timeout(2000)
            if "login" not in self.page.url.lower():
                print("\n[OK] Login successful!")
                return True
            remaining = int(timeout_seconds - (asyncio.get_event_loop().time() - start))
            if remaining % 20 == 0 and remaining > 0:
                print(f"  Waiting... {remaining}s remaining")

        print("[WARN] Login timeout")
        return False

    async def extract_videos_from_page(self, source_name=""):
        """Extract video data from current page DOM"""
        videos = await self.page.evaluate('''() => {
            const videos = [];

            // Try multiple selectors for video cards
            const selectors = [
                'a[href*="/videos/"]',
                '[class*="video-card"] a',
                '[class*="VideoCard"] a',
                '[class*="thumbnail-container"] a',
                '[data-testid*="video"] a',
                '.grid a[href*="/"]',
                '[class*="episode"] a',
                '[class*="Episode"] a',
            ];

            const seen = new Set();

            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => {
                    const href = el.getAttribute('href');
                    if (!href || seen.has(href)) return;

                    // Only video links
                    if (!href.includes('/videos/') && !href.includes('/watch/')) return;

                    seen.add(href);

                    // Get title from various sources
                    const titleEl = el.querySelector('h1, h2, h3, h4, [class*="title"], [class*="Title"]');
                    const title = titleEl?.textContent?.trim() ||
                                 el.getAttribute('title') ||
                                 el.getAttribute('aria-label') ||
                                 '';

                    // Get thumbnail
                    const imgEl = el.querySelector('img');
                    const thumbnail = imgEl?.src || imgEl?.getAttribute('data-src') || '';

                    // Get duration
                    const durEl = el.querySelector('[class*="duration"], [class*="Duration"], [class*="time"]');
                    const duration = durEl?.textContent?.trim() || '';

                    // Extract slug/id from URL
                    const slug = href.split('/').pop()?.split('?')[0] || '';

                    videos.push({
                        url: href.startsWith('http') ? href : 'https://www.pokergo.com' + href,
                        slug: slug,
                        title: title,
                        thumbnail: thumbnail,
                        duration: duration,
                    });
                });
            });

            return videos;
        }''')

        # Add source and deduplicate
        new_videos = []
        for v in videos:
            v['source'] = source_name
            if not any(existing.get('url') == v.get('url') for existing in self.all_videos):
                self.all_videos.append(v)
                new_videos.append(v)

        return new_videos

    async def scroll_and_collect(self, max_scrolls=20):
        """Scroll page and collect videos"""
        prev_count = len(self.all_videos)

        for i in range(max_scrolls):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(2000)

            # Check for new content (side effect: adds to self.all_videos)
            _current = await self.extract_videos_from_page()

            # Check if we've stopped finding new content
            if i > 5 and len(self.all_videos) == prev_count:
                break

        return len(self.all_videos) - prev_count

    async def scrape_wsop(self):
        """Scrape all WSOP content"""

        # URLs to visit
        urls = [
            ("WSOP Main", "https://www.pokergo.com/wsop"),
            ("WSOP Shows", "https://www.pokergo.com/shows/wsop"),
            ("Search WSOP", "https://www.pokergo.com/search?q=WSOP"),
        ]

        # Add year-specific pages
        for year in range(2025, 2010, -1):
            urls.append((f"WSOP {year}", f"https://www.pokergo.com/shows/wsop-{year}"))
            urls.append((f"Search {year}", f"https://www.pokergo.com/search?q=WSOP+{year}"))
            urls.append((f"Collection {year} ME", f"https://www.pokergo.com/collections/wsop-{year}-main-event"))
            urls.append((f"Collection {year} BE", f"https://www.pokergo.com/collections/wsop-{year}-bracelet-events"))

        for name, url in urls:
            print(f"\n[SCRAPING] {name}")
            print(f"  URL: {url}")

            prev_count = len(self.all_videos)

            try:
                await self.page.goto(url, wait_until="networkidle", timeout=30000)
                await self.page.wait_for_timeout(3000)

                # Extract from initial page
                await self.extract_videos_from_page(name)

                # Scroll for more content
                await self.scroll_and_collect(max_scrolls=15)

                added = len(self.all_videos) - prev_count
                print(f"  [OK] +{added} videos (total: {len(self.all_videos)})")

            except Exception as e:
                print(f"  [ERROR] {str(e)[:100]}")

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    def save_data(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Extract year from title
        for v in self.all_videos:
            title = v.get('title', '')
            for year in range(2011, 2026):
                if str(year) in title:
                    v['year'] = year
                    break

        # Count by year
        year_counts = {}
        for v in self.all_videos:
            y = v.get('year', 'unknown')
            year_counts[y] = year_counts.get(y, 0) + 1

        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(self.all_videos),
            "by_year": year_counts,
            "videos": self.all_videos,
        }

        output_file = OUTPUT_DIR / f"wsop_dom_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[RESULT]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print(f"  Total: {len(self.all_videos)} videos")
        print("\n[BY YEAR]")
        for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
            print(f"  {y}: {c}")

        return output_file


async def main():
    print("=" * 60)
    print("PokerGO WSOP DOM Scraper")
    print("=" * 60)

    scraper = DOMScraper()

    try:
        await scraper.start()

        # Interactive login
        logged_in = await scraper.login_interactive(timeout_seconds=120)

        if logged_in:
            await scraper.scrape_wsop()
            scraper.save_data()
        else:
            print("[ERROR] Login failed. Cannot scrape premium content.")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
