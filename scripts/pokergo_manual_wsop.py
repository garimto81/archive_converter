"""
PokerGO WSOP 스크래퍼 - 수동 로그인 방식

브라우저에서 직접 로그인 후 데이터 수집
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ManualWSOPScraper:
    def __init__(self):
        self.browser = None
        self.page = None
        self.all_videos = []
        self.api_responses = []

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()

        # API 응답 캡처
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

        def process_item(item):
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
                "description": item.get("description", "")[:200] if item.get("description") else "",
                "slug": item.get("slug", ""),
                "duration": item.get("duration"),
                "aired_at": item.get("aired_at"),
                "show_name": item.get("show_name", ""),
                "show_year": item.get("show_year"),
                "show_season": item.get("show_season"),
                "show_episode_number": item.get("show_episode_number"),
                "video_type": item.get("video_type", ""),
                "type": item.get("type", ""),
                "source_api": source_url[:100],
            }

            # 이미지 URL
            images = item.get("images", {})
            if images and isinstance(images, dict):
                video["thumbnail"] = images.get("thumbnail") or images.get("poster") or ""

            self.all_videos.append(video)

        # 다양한 구조 탐색
        if "data" in data:
            inner = data["data"]
            if isinstance(inner, list):
                for item in inner:
                    process_item(item)
            elif isinstance(inner, dict):
                for key in ["videos", "recently_added", "trending", "recommended", "view_videos", "results"]:
                    if key in inner and inner[key]:
                        items = inner[key]
                        if isinstance(items, list):
                            for item in items:
                                process_item(item)

                # view_collections
                if "view_collections" in inner and inner["view_collections"]:
                    for coll in inner["view_collections"]:
                        if "videos" in coll and coll["videos"]:
                            for v in coll["videos"]:
                                process_item(v)

        # 최상위 레벨의 videos
        if "videos" in data and isinstance(data["videos"], list):
            for item in data["videos"]:
                process_item(item)

        # results (검색 결과)
        if "results" in data and isinstance(data["results"], list):
            for item in data["results"]:
                process_item(item)

    async def manual_login(self):
        """수동 로그인 대기 (60초)"""
        print("\n" + "=" * 60)
        print("MANUAL LOGIN REQUIRED")
        print("=" * 60)
        print("1. Browser will open PokerGO login page")
        print("2. Please log in manually within 60 seconds")
        print("=" * 60)

        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")

        # 60초 동안 대기하면서 로그인 상태 확인
        for i in range(60):
            await self.page.wait_for_timeout(1000)
            current_url = self.page.url

            if "login" not in current_url.lower():
                print(f"\n[OK] Login confirmed! (after {i+1} seconds)")
                return True

            if i % 10 == 9:
                print(f"  Waiting... {60-i-1} seconds remaining")

        print("[WARN] Timeout - continuing without confirmed login")
        return False

    async def scrape_wsop_pages(self):
        """WSOP 관련 페이지들 스크래핑"""

        pages = [
            ("Home", "https://www.pokergo.com/"),
            ("Shows", "https://www.pokergo.com/shows"),
            ("WSOP Main", "https://www.pokergo.com/wsop"),
            ("WSOP Show", "https://www.pokergo.com/shows/wsop"),
            ("WSOP 2024", "https://www.pokergo.com/shows/wsop-2024"),
            ("WSOP 2023", "https://www.pokergo.com/shows/wsop-2023"),
            ("WSOP Main Event", "https://www.pokergo.com/shows/wsop-main-event"),
            ("Search WSOP", "https://www.pokergo.com/search?q=WSOP"),
        ]

        for name, url in pages:
            print(f"\n[SCRAPING] {name}: {url}")
            try:
                await self.page.goto(url, wait_until="networkidle")
                await self.page.wait_for_timeout(3000)

                # 스크롤로 더 많은 콘텐츠 로드
                prev_count = len(self.all_videos)
                for i in range(10):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1500)

                new_count = len(self.all_videos)
                print(f"  [OK] Videos so far: {new_count} (+{new_count - prev_count})")

            except Exception as e:
                print(f"  [ERROR] {e}")

        # 검색 쿼리들
        search_queries = ["WSOP 2024", "WSOP 2023", "WSOP 2022", "WSOP 2021", "WSOP Main Event", "WSOP Bracelet"]
        for query in search_queries:
            print(f"\n[SEARCH] {query}")
            try:
                await self.page.goto(f"https://www.pokergo.com/search?q={query}", wait_until="networkidle")
                await self.page.wait_for_timeout(3000)

                for _ in range(5):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1000)

                print(f"  [OK] Videos so far: {len(self.all_videos)}")
            except Exception as e:
                print(f"  [ERROR] {e}")

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    def save_data(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # WSOP 필터링
        wsop_videos = []
        other_videos = []

        for v in self.all_videos:
            title = (v.get("title") or "").lower()
            show = (v.get("show_name") or "").lower()

            if "wsop" in title or "wsop" in show or "world series" in title:
                v["is_wsop"] = True
                wsop_videos.append(v)
            else:
                v["is_wsop"] = False
                other_videos.append(v)

        # 전체 저장
        all_file = OUTPUT_DIR / f"pokergo_all_{timestamp}.json"
        with open(all_file, "w", encoding="utf-8") as f:
            json.dump({
                "scraped_at": datetime.now().isoformat(),
                "total": len(self.all_videos),
                "wsop_count": len(wsop_videos),
                "other_count": len(other_videos),
                "videos": self.all_videos
            }, f, ensure_ascii=False, indent=2)

        # WSOP만 저장
        wsop_file = OUTPUT_DIR / f"wsop_only_{timestamp}.json"
        with open(wsop_file, "w", encoding="utf-8") as f:
            json.dump({
                "scraped_at": datetime.now().isoformat(),
                "total": len(wsop_videos),
                "videos": wsop_videos
            }, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[SAVED]")
        print(f"{'='*60}")
        print(f"  All videos: {all_file}")
        print(f"  WSOP only: {wsop_file}")
        print("\n[STATS]")
        print(f"  Total videos: {len(self.all_videos)}")
        print(f"  WSOP videos: {len(wsop_videos)}")
        print(f"  Other videos: {len(other_videos)}")
        print(f"  API responses: {len(self.api_responses)}")

        return wsop_file


async def main():
    print("=" * 60)
    print("PokerGO WSOP Scraper - Manual Login")
    print("=" * 60)

    scraper = ManualWSOPScraper()

    try:
        await scraper.start()
        await scraper.manual_login()
        await scraper.scrape_wsop_pages()
        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
