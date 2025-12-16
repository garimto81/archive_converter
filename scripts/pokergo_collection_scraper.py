"""
PokerGO WSOP Collection Scraper

기존에 성공한 collection URL들을 사용하여 데이터 수집
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

# 성공적으로 수집된 collection URLs (12/15 데이터 기준)
COLLECTION_URLS = [
    # 2025
    ("2025", "Main Event", "https://www.pokergo.com/collections/wsop-2025-main-event"),
    ("2025", "Bracelet Events", "https://www.pokergo.com/collections/wsop-2025-bracelet-events"),
    # 2024
    ("2024", "Main Event Episodes", "https://www.pokergo.com/collections/wsop-2024-main-event--episodes"),
    ("2024", "Main Event Livestreams", "https://www.pokergo.com/collections/wsop-2024-main-event"),
    ("2024", "Bracelet Episodes", "https://www.pokergo.com/collections/wsop-2024-bracelet-events--episodes"),
    ("2024", "Bracelet Livestreams", "https://www.pokergo.com/collections/wsop-2024-bracelet-events"),
    # 2023
    ("2023", "Main Event", "https://www.pokergo.com/collections/wsop-2023-main-event"),
    ("2023", "Bracelet Events", "https://www.pokergo.com/collections/wsop-2023-bracelet-events"),
    # 2022
    ("2022", "Main Event", "https://www.pokergo.com/collections/wsop-2022-main-event"),
    ("2022", "Bracelet Events", "https://www.pokergo.com/collections/wsop-2022-bracelet-events"),
    # 2021
    ("2021", "Main Event", "https://www.pokergo.com/collections/wsop-2021-main-event"),
    ("2021", "Bracelet Events", "https://www.pokergo.com/collections/wsop-2021-bracelet-events"),
    # 2019
    ("2019", "Main Event", "https://www.pokergo.com/collections/wsop-2019-main-event"),
    ("2019", "Bracelet Events", "https://www.pokergo.com/collections/wsop-2019-bracelet-events"),
    # 2018
    ("2018", "Main Event", "https://www.pokergo.com/collections/wsop-2018-main-event"),
    # 2017
    ("2017", "Main Event", "https://www.pokergo.com/collections/wsop-2017-main-event"),
    # 2016
    ("2016", "Main Event", "https://www.pokergo.com/collections/wsop-2016-main-event"),
    # 2015
    ("2015", "Main Event", "https://www.pokergo.com/collections/wsop-2015-main-event"),
    # 2014
    ("2014", "Main Event", "https://www.pokergo.com/collections/wsop-2014-main-event"),
    # 2013
    ("2013", "Main Event", "https://www.pokergo.com/collections/wsop-2013-main-event"),
    # 2012
    ("2012", "Main Event", "https://www.pokergo.com/collections/wsop-2012-main-event"),
    # 2011
    ("2011", "Main Event", "https://www.pokergo.com/collections/wsop-2011-main-event"),
]


class CollectionScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.all_videos = []
        self.api_responses = []
        self.logged_in = False

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()
        self.page.on("response", self._capture_response)
        print("[INFO] Browser started")

    async def _capture_response(self, response):
        url = response.url
        if "api.pokergo.com" in url and response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.api_responses.append({"url": url, "data": data})
                    self._extract_videos(data, url)
            except Exception:
                pass

    def _extract_videos(self, data, source_url):
        if not isinstance(data, dict):
            return

        def process_item(item, source=""):
            if not isinstance(item, dict):
                return
            video_id = item.get("id")
            if not video_id:
                return
            if any(v.get("id") == video_id for v in self.all_videos):
                return

            video = {
                "id": video_id,
                "title": item.get("title", ""),
                "description": (item.get("description") or "")[:300],
                "slug": item.get("slug", ""),
                "duration": item.get("duration"),
                "aired_at": item.get("aired_at"),
                "show_name": item.get("show_name", ""),
                "show_year": item.get("show_year"),
                "show_season": item.get("show_season"),
                "show_episode_number": item.get("show_episode_number"),
                "video_type": item.get("video_type", ""),
                "type": item.get("type", ""),
                "url": f"https://www.pokergo.com/videos/{item.get('slug', video_id)}",
                "source_collection": source,
            }

            images = item.get("images", {})
            if images and isinstance(images, dict):
                video["thumbnail"] = images.get("thumbnail") or images.get("poster") or ""

            self.all_videos.append(video)

        # Parse various API response structures
        if "data" in data:
            inner = data["data"]
            if isinstance(inner, list):
                for item in inner:
                    process_item(item, source_url)
            elif isinstance(inner, dict):
                for key in ["videos", "results", "items", "view_videos"]:
                    if key in inner and isinstance(inner[key], list):
                        for item in inner[key]:
                            process_item(item, source_url)

                if "view_collections" in inner:
                    for coll in inner.get("view_collections", []):
                        if "videos" in coll:
                            for v in coll["videos"]:
                                process_item(v, source_url)

        # Top-level structures
        for key in ["videos", "results", "items"]:
            if key in data and isinstance(data[key], list):
                for item in data[key]:
                    process_item(item, source_url)

    async def login(self):
        if not POKERGO_ID or not POKERGO_PASSWORD:
            print("[WARN] No credentials in .env")
            return False

        print(f"[INFO] Logging in: {POKERGO_ID}")
        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await self.page.wait_for_timeout(2000)

        try:
            # Fill email
            email = await self.page.query_selector('input[type="email"], input[name="email"]')
            if email:
                await email.fill(POKERGO_ID)
                await self.page.wait_for_timeout(300)

            # Fill password
            pwd = await self.page.query_selector('input[type="password"]')
            if pwd:
                await pwd.fill(POKERGO_PASSWORD)
                await self.page.wait_for_timeout(300)

            # Click login
            btn = await self.page.query_selector('button[type="submit"]')
            if btn:
                await btn.click()
                await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url.lower():
                print("[OK] Login successful!")
                self.logged_in = True
                return True
        except Exception as e:
            print(f"[ERROR] Login failed: {e}")

        print("[WARN] Login may have failed")
        return False

    async def scrape_collections(self):
        print(f"\n[INFO] Scraping {len(COLLECTION_URLS)} collections...")

        for year, category, url in COLLECTION_URLS:
            print(f"\n[{year}] {category}")
            print(f"  URL: {url}")

            prev_count = len(self.all_videos)

            try:
                await self.page.goto(url, wait_until="networkidle")
                await self.page.wait_for_timeout(3000)

                # Scroll to load more
                for i in range(15):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1000)

                new_count = len(self.all_videos)
                added = new_count - prev_count
                print(f"  [OK] +{added} videos (total: {new_count})")

            except Exception as e:
                print(f"  [ERROR] {e}")

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    def save_data(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Year stats
        year_counts = {}
        for v in self.all_videos:
            year = v.get("show_year")
            if not year:
                # Extract from title
                title = v.get("title", "")
                for y in range(2011, 2026):
                    if str(y) in title:
                        year = y
                        break
            year_counts[year] = year_counts.get(year, 0) + 1

        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(self.all_videos),
            "by_year": dict(sorted(year_counts.items(), key=lambda x: (x[0] or 0), reverse=True)),
            "videos": self.all_videos,
        }

        output_file = OUTPUT_DIR / f"wsop_collection_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[SAVED]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print("\n[STATS]")
        print(f"  Total videos: {len(self.all_videos)}")
        print("\n[BY YEAR]")
        for year, count in sorted(year_counts.items(), key=lambda x: (x[0] or 0), reverse=True):
            print(f"  {year}: {count}")

        return output_file


async def main():
    print("=" * 60)
    print("PokerGO WSOP Collection Scraper")
    print("=" * 60)

    scraper = CollectionScraper()

    try:
        await scraper.start()
        await scraper.login()
        await scraper.scrape_collections()
        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
