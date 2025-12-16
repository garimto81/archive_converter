"""
PokerGO API를 통한 WSOP 데이터 수집

API 직접 호출로 전체 WSOP 비디오 목록 수집
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

# PokerGO API 엔드포인트
API_BASE = "https://api.pokergo.com/v4/api"


class PokerGoAPIClient:
    """PokerGO API 클라이언트"""

    def __init__(self):
        self.browser = None
        self.page = None
        self.auth_token = None
        self.all_videos = []
        self.api_responses = []

    async def start(self):
        """브라우저 시작 및 로그인"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()

        # API 응답 캡처
        self.page.on("response", self._capture_response)

        print("[INFO] Browser started")

    async def _capture_response(self, response):
        """API 응답 캡처"""
        url = response.url
        if "api.pokergo.com" in url and response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.api_responses.append({"url": url, "data": data})

                    # 비디오 데이터 추출
                    self._extract_videos(data, url)
            except Exception:
                pass

    def _extract_videos(self, data, source_url):
        """API 응답에서 비디오 추출"""
        if not isinstance(data, dict):
            return

        # data 키 내부 탐색
        if "data" in data:
            inner = data["data"]
            if isinstance(inner, list):
                for item in inner:
                    self._process_video_item(item, source_url)
            elif isinstance(inner, dict):
                # 홈페이지 구조
                for key in ["recently_added", "trending", "recommended", "view_videos"]:
                    if key in inner and inner[key]:
                        for item in inner[key]:
                            self._process_video_item(item, source_url)

                # view_collections 내의 videos
                if "view_collections" in inner and inner["view_collections"]:
                    for coll in inner["view_collections"]:
                        if "videos" in coll and coll["videos"]:
                            for v in coll["videos"]:
                                self._process_video_item(v, source_url)

    def _process_video_item(self, item, source_url):
        """비디오 아이템 처리"""
        if not isinstance(item, dict):
            return

        video_id = item.get("id")
        if not video_id:
            return

        # 중복 체크
        if any(v.get("id") == video_id for v in self.all_videos):
            return

        video = {
            "id": video_id,
            "title": item.get("title", ""),
            "description": item.get("description", ""),
            "slug": item.get("slug", ""),
            "duration": item.get("duration"),
            "aired_at": item.get("aired_at"),
            "show_name": item.get("show_name", ""),
            "show_year": item.get("show_year"),
            "show_season": item.get("show_season"),
            "show_episode_number": item.get("show_episode_number"),
            "video_type": item.get("video_type", ""),
            "type": item.get("type", ""),
            "images": item.get("images", {}),
            "source_api": source_url,
        }

        # WSOP 관련 필터링
        title_lower = video["title"].lower() if video["title"] else ""
        show_lower = video["show_name"].lower() if video["show_name"] else ""

        if "wsop" in title_lower or "wsop" in show_lower or "world series" in title_lower:
            video["is_wsop"] = True
        else:
            video["is_wsop"] = False

        self.all_videos.append(video)

    async def login(self):
        """로그인"""
        print(f"[INFO] Logging in as {POKERGO_ID}...")

        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        email_input = await self.page.query_selector('input[type="email"]')
        if email_input:
            await email_input.fill(POKERGO_ID)

        pwd_input = await self.page.query_selector('input[type="password"]')
        if pwd_input:
            await pwd_input.fill(POKERGO_PASSWORD)

        login_btn = await self.page.query_selector('button[type="submit"]')
        if login_btn:
            await login_btn.click()
            await self.page.wait_for_timeout(5000)

        if "login" not in self.page.url.lower():
            print("[OK] Login successful!")
            return True

        print("[WARN] Login may have failed")
        return False

    async def fetch_search_results(self, query: str, page_num: int = 1):
        """검색 API 호출"""
        print(f"  [SEARCH] '{query}' page {page_num}...")

        # 검색 페이지로 이동
        search_url = f"https://www.pokergo.com/search?q={query}&page={page_num}"
        await self.page.goto(search_url, wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 스크롤
        for _ in range(5):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1500)

    async def fetch_shows_page(self):
        """쇼 목록 페이지"""
        print("[INFO] Fetching shows page...")

        await self.page.goto("https://www.pokergo.com/shows", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        for _ in range(10):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1500)

    async def fetch_collections(self):
        """컬렉션 페이지들 방문"""
        print("[INFO] Fetching collection pages...")

        # WSOP 관련 페이지들
        urls = [
            "https://www.pokergo.com/wsop",
            "https://www.pokergo.com/collections/wsop-2024",
            "https://www.pokergo.com/collections/wsop-2023",
            "https://www.pokergo.com/collections/wsop-2022",
            "https://www.pokergo.com/shows/wsop",
            "https://www.pokergo.com/shows/wsop-main-event",
            "https://www.pokergo.com/shows/wsop-bracelet-events",
        ]

        for url in urls:
            print(f"  [VISIT] {url}")
            try:
                await self.page.goto(url, wait_until="networkidle")
                await self.page.wait_for_timeout(2000)

                for _ in range(5):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1000)
            except Exception as e:
                print(f"    [WARN] Error: {e}")

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    def save_data(self):
        """데이터 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 전체 비디오
        all_file = OUTPUT_DIR / f"pokergo_all_videos_{timestamp}.json"
        with open(all_file, "w", encoding="utf-8") as f:
            json.dump({
                "scraped_at": datetime.now().isoformat(),
                "total_videos": len(self.all_videos),
                "videos": self.all_videos
            }, f, ensure_ascii=False, indent=2)

        # WSOP만 필터링
        wsop_videos = [v for v in self.all_videos if v.get("is_wsop")]
        wsop_file = OUTPUT_DIR / f"wsop_videos_{timestamp}.json"
        with open(wsop_file, "w", encoding="utf-8") as f:
            json.dump({
                "scraped_at": datetime.now().isoformat(),
                "total_videos": len(wsop_videos),
                "videos": wsop_videos
            }, f, ensure_ascii=False, indent=2)

        # API 응답 (디버깅용)
        api_file = OUTPUT_DIR / f"pokergo_api_raw_{timestamp}.json"
        with open(api_file, "w", encoding="utf-8") as f:
            json.dump(self.api_responses, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[OK] Data saved!")
        print(f"{'='*60}")
        print(f"  All videos: {all_file}")
        print(f"  WSOP videos: {wsop_file}")
        print(f"  API raw: {api_file}")
        print("\n[STATS]")
        print(f"  Total videos: {len(self.all_videos)}")
        print(f"  WSOP videos: {len(wsop_videos)}")
        print(f"  API responses: {len(self.api_responses)}")

        return wsop_file


async def main():
    print("=" * 60)
    print("PokerGO WSOP Data Collection via API")
    print("=" * 60)

    client = PokerGoAPIClient()

    try:
        await client.start()
        await client.login()

        # 다양한 페이지 방문하여 API 응답 수집
        await client.fetch_shows_page()
        await client.fetch_collections()

        # 검색으로 WSOP 비디오 수집
        for query in ["WSOP", "World Series of Poker", "WSOP 2024", "WSOP 2023", "WSOP Main Event"]:
            await client.fetch_search_results(query, 1)
            await client.fetch_search_results(query, 2)
            await client.fetch_search_results(query, 3)

        # 저장
        client.save_data()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
