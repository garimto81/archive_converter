"""
PokerGO WSOP 전체 스크래퍼

WSOP 이벤트 페이지의 모든 시즌, 이벤트, 비디오를 수집합니다.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, Browser

# .env 파일 로드
load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class WSOPScraper:
    """WSOP 전체 스크래퍼"""

    BASE_URL = "https://www.pokergo.com"
    WSOP_URL = "https://www.pokergo.com/wsop"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.api_responses: list = []
        self.collected_data: dict = {
            "scraped_at": None,
            "source": "WSOP",
            "years": [],
            "events": [],
            "videos": [],
            "total_videos": 0,
        }

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()

        # API 응답 캡처
        self.page.on("response", self._capture_response)

        print("[INFO] Browser started")

    async def _capture_response(self, response):
        """API 응답 캡처"""
        url = response.url
        if response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    self.api_responses.append({
                        "url": url,
                        "data": data,
                    })
            except Exception:
                pass

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    async def login(self) -> bool:
        """PokerGO 로그인"""
        if not POKERGO_ID or not POKERGO_PASSWORD:
            print("[WARN] No credentials found in .env, skipping login")
            return False

        print(f"[INFO] Logging in: {POKERGO_ID}")

        try:
            await self.page.goto(f"{self.BASE_URL}/login", wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 이메일 입력
            email_input = await self.page.query_selector('input[type="email"], input[name="email"], input[placeholder*="mail"]')
            if email_input:
                await email_input.fill(POKERGO_ID)
                await self.page.wait_for_timeout(300)

            # 비밀번호 입력
            pwd_input = await self.page.query_selector('input[type="password"]')
            if pwd_input:
                await pwd_input.fill(POKERGO_PASSWORD)
                await self.page.wait_for_timeout(300)

            # 로그인 버튼 찾기
            login_btn = await self.page.query_selector('button[type="submit"], button:has-text("Login"), button:has-text("Sign"), button:has-text("LOG")')
            if login_btn:
                await login_btn.click()
                await self.page.wait_for_timeout(5000)

            if "login" not in self.page.url.lower():
                print("[OK] Login successful!")
                return True

        except Exception as e:
            print(f"[WARN] Login error: {e}")

        print("[WARN] Login skipped, continuing without login")
        return False

    async def scroll_to_bottom(self, max_scrolls: int = 20):
        """페이지 끝까지 스크롤"""
        prev_height = 0
        for i in range(max_scrolls):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1500)

            curr_height = await self.page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                print(f"  [OK] Scroll complete at {i+1} scrolls")
                break
            prev_height = curr_height

    async def scrape_wsop_main(self):
        """WSOP 메인 페이지 스크래핑"""
        print("\n[INFO] Scraping WSOP main page...")

        await self.page.goto(self.WSOP_URL, wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 연도별 링크 추출
        years = await self.page.evaluate('''() => {
            const years = [];
            // WSOP 연도별 섹션 찾기
            document.querySelectorAll('a[href*="/wsop/"]').forEach(link => {
                const href = link.getAttribute("href");
                const text = link.textContent?.trim();

                // 연도 패턴 확인 (2024, 2023 등)
                const yearMatch = href.match(/wsop\/(\d{4})/);
                if (yearMatch) {
                    const year = yearMatch[1];
                    if (!years.find(y => y.year === year)) {
                        years.push({
                            year: year,
                            url: href.startsWith("http") ? href : "https://www.pokergo.com" + href,
                            title: text
                        });
                    }
                }
            });
            return years.sort((a, b) => b.year - a.year);
        }''')

        print(f"  [OK] Found {len(years)} years: {[y['year'] for y in years]}")
        self.collected_data["years"] = years
        return years

    async def scrape_year_page(self, year_url: str, year: str):
        """연도별 WSOP 페이지 스크래핑"""
        print(f"\n[INFO] Scraping WSOP {year}...")

        await self.page.goto(year_url, wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 디버깅: 현재 URL과 페이지 제목 출력
        current_url = self.page.url
        title = await self.page.title()
        print(f"  [DEBUG] URL: {current_url}")
        print(f"  [DEBUG] Title: {title}")

        # 무한 스크롤
        await self.scroll_to_bottom(max_scrolls=30)

        # 모든 a 태그 수집 (디버깅용)
        all_links = await self.page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a').forEach(link => {
                const href = link.getAttribute("href");
                if (href) links.push(href);
            });
            return links;
        }''')

        # 비디오 관련 링크 필터링
        video_links = [link for link in all_links if "/videos/" in link or "/watch/" in link or "video" in link.lower()]
        print(f"  [DEBUG] Total links: {len(all_links)}, Video-related: {len(video_links)}")

        if video_links[:5]:
            print(f"  [DEBUG] Sample links: {video_links[:5]}")

        # 이벤트 및 비디오 추출 (더 넓은 셀렉터)
        data = await self.page.evaluate('''(year) => {
            const events = [];
            const videos = [];

            // 모든 비디오 링크 수집 (다양한 패턴)
            const selectors = [
                'a[href*="/videos/"]',
                'a[href*="/watch/"]',
                'a[href*="video"]',
                '[data-video]',
                '[class*="video"] a',
                '[class*="card"] a',
                '[class*="episode"] a',
                '[class*="thumbnail"] a'
            ];

            selectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(link => {
                        const href = link.getAttribute("href") || link.closest("a")?.getAttribute("href");
                        if (!href) return;

                        const title = link.querySelector("[class*='title'], h2, h3, h4, p, span")?.textContent?.trim() ||
                                     link.getAttribute("title") ||
                                     link.getAttribute("aria-label") ||
                                     link.textContent?.trim()?.substring(0, 200);
                        const thumbnail = link.querySelector("img")?.src ||
                                         link.querySelector("[style*='background']")?.style?.backgroundImage;
                        const duration = link.querySelector("[class*='duration'], [class*='time'], [class*='length']")?.textContent?.trim();

                        const fullUrl = href.startsWith("http") ? href : "https://www.pokergo.com" + href;

                        if (!videos.find(v => v.url === fullUrl)) {
                            videos.push({
                                url: fullUrl,
                                video_id: href.split("/").pop()?.split("?")[0],
                                title: title || "Unknown",
                                thumbnail: thumbnail,
                                duration: duration,
                                year: year,
                                source: "wsop",
                                selector_matched: selector
                            });
                        }
                    });
                } catch(e) {}
            });

            return { events, videos };
        }''', year)

        print(f"  [OK] Found {len(data['videos'])} videos, {len(data['events'])} events")
        return data

    async def scrape_video_details(self, video_url: str) -> dict:
        """개별 비디오 상세 정보 스크래핑"""
        try:
            await self.page.goto(video_url, wait_until="networkidle")
            await self.page.wait_for_timeout(1500)

            details = await self.page.evaluate('''() => {
                const details = {};

                // 제목
                details.title = document.querySelector("h1, [class*='title']")?.textContent?.trim();

                // 설명
                details.description = document.querySelector("[class*='description'], [class*='synopsis'], p")?.textContent?.trim();

                // 메타데이터
                const metaElements = document.querySelectorAll("[class*='meta'], [class*='info'], [class*='detail']");
                metaElements.forEach(el => {
                    const text = el.textContent?.trim();
                    if (text) {
                        // 날짜 패턴
                        const dateMatch = text.match(/(\d{1,2}\/\d{1,2}\/\d{4}|\w+ \d{1,2}, \d{4})/);
                        if (dateMatch) details.air_date = dateMatch[1];

                        // 시간 패턴
                        const durationMatch = text.match(/(\d+:\d+:\d+|\d+ ?hr|\d+ ?min)/i);
                        if (durationMatch) details.duration = durationMatch[1];
                    }
                });

                // 태그/카테고리
                const tags = [];
                document.querySelectorAll("[class*='tag'], [class*='category'], [class*='badge']").forEach(el => {
                    const tag = el.textContent?.trim();
                    if (tag && tag.length < 50) tags.push(tag);
                });
                details.tags = tags;

                // 시즌/에피소드
                const breadcrumb = document.querySelector("[class*='breadcrumb']")?.textContent;
                if (breadcrumb) details.breadcrumb = breadcrumb;

                return details;
            }''')

            return details
        except Exception as e:
            print(f"    [WARN] Failed to get details: {e}")
            return {}

    async def scrape_all_wsop(self, get_details: bool = False, max_videos_per_year: int = None):
        """전체 WSOP 데이터 스크래핑"""

        # WSOP 메인 페이지에서 연도 목록
        years = await self.scrape_wsop_main()

        if not years:
            # 연도를 직접 지정
            print("[INFO] No years found, trying manual year list...")
            years = [
                {"year": str(y), "url": f"{self.WSOP_URL}/{y}", "title": f"WSOP {y}"}
                for y in range(2024, 2014, -1)  # 2024 ~ 2015
            ]

        all_videos = []
        all_events = []

        for year_info in years:
            year = year_info["year"]
            year_url = year_info["url"]

            data = await self.scrape_year_page(year_url, year)

            # 비디오 제한
            videos = data["videos"]
            if max_videos_per_year and len(videos) > max_videos_per_year:
                videos = videos[:max_videos_per_year]

            # 상세 정보 수집 (선택적)
            if get_details:
                print(f"  [INFO] Getting details for {len(videos)} videos...")
                for i, video in enumerate(videos):
                    if i % 10 == 0:
                        print(f"    [{i+1}/{len(videos)}]")
                    details = await self.scrape_video_details(video["url"])
                    video.update(details)
                    await self.page.wait_for_timeout(500)  # Rate limiting

            all_videos.extend(videos)
            all_events.extend(data["events"])

            print(f"  [TOTAL] {len(all_videos)} videos collected so far")

        self.collected_data["videos"] = all_videos
        self.collected_data["events"] = all_events
        self.collected_data["total_videos"] = len(all_videos)

    def deduplicate(self):
        """중복 제거"""
        seen_urls = set()
        unique_videos = []
        for v in self.collected_data["videos"]:
            url = v.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_videos.append(v)

        before = len(self.collected_data["videos"])
        self.collected_data["videos"] = unique_videos
        self.collected_data["total_videos"] = len(unique_videos)

        if before != len(unique_videos):
            print(f"[INFO] Deduplicated: {before} -> {len(unique_videos)}")

    def save_data(self) -> Path:
        """데이터 저장"""
        self.collected_data["scraped_at"] = datetime.now().isoformat()
        self.deduplicate()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 메인 데이터
        main_file = OUTPUT_DIR / f"wsop_full_{timestamp}.json"
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

        # API 응답 (디버깅용)
        if self.api_responses:
            api_file = OUTPUT_DIR / f"wsop_api_{timestamp}.json"
            with open(api_file, "w", encoding="utf-8") as f:
                json.dump(self.api_responses, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[OK] Scraping complete!")
        print(f"{'='*60}")
        print(f"  Output: {main_file}")
        print("\n[STATS]")
        print(f"  - Years: {len(self.collected_data['years'])}")
        print(f"  - Events: {len(self.collected_data['events'])}")
        print(f"  - Videos: {self.collected_data['total_videos']}")

        # 연도별 통계
        year_counts = {}
        for v in self.collected_data["videos"]:
            y = v.get("year", "unknown")
            year_counts[y] = year_counts.get(y, 0) + 1

        print("\n[BY YEAR]")
        for y in sorted(year_counts.keys(), reverse=True):
            print(f"  - {y}: {year_counts[y]} videos")

        return main_file


async def main():
    print("=" * 60)
    print("PokerGO WSOP Full Scraper")
    print("=" * 60)

    scraper = WSOPScraper(headless=False)

    try:
        await scraper.start()

        # 로그인 시도
        await scraper.login()

        # WSOP 전체 스크래핑
        await scraper.scrape_all_wsop(
            get_details=False,  # 상세 정보 수집 (느림)
            max_videos_per_year=None  # 연도당 최대 비디오 수 (None=무제한)
        )

        # 저장
        _output_file = scraper.save_data()  # returns saved file path

        print("\n[NEXT STEP]")
        print("  Run: python scripts/upload_wsop_to_sheets.py")

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
