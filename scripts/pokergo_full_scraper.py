"""
PokerGO 전체 스크래퍼

페이지 콘텐츠와 API 응답 모두 캡처합니다.
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


class PokerGoFullScraper:
    """PokerGO 전체 스크래퍼"""

    BASE_URL = "https://www.pokergo.com"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.all_api_responses: list = []
        self.collected_data: dict = {
            "scraped_at": None,
            "shows": [],
            "videos": [],
            "seasons": [],
        }

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()

        # 모든 응답 캡처
        self.page.on("response", self._capture_response)

        print("[INFO] 브라우저 시작")

    async def _capture_response(self, response):
        """모든 API 응답 캡처"""
        url = response.url
        # JSON 응답만 캡처
        if response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    self.all_api_responses.append({
                        "url": url,
                        "data": data,
                    })
            except Exception:
                pass

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] 브라우저 종료")

    async def login(self) -> bool:
        """PokerGO 로그인"""
        print(f"[INFO] 로그인: {POKERGO_ID}")

        await self.page.goto(f"{self.BASE_URL}/login", wait_until="networkidle")
        await self.page.wait_for_timeout(2000)

        # 이메일 입력
        await self.page.fill('input[type="email"], input[name="email"], input:first-of-type', POKERGO_ID)
        await self.page.wait_for_timeout(300)

        # 비밀번호 입력
        await self.page.fill('input[type="password"]', POKERGO_PASSWORD)
        await self.page.wait_for_timeout(300)

        # 로그인 버튼
        await self.page.click('button:has-text("LOGIN"), button:has-text("Sign In"), button[type="submit"]')
        await self.page.wait_for_timeout(5000)

        if "login" not in self.page.url.lower():
            print("[SUCCESS] 로그인 성공!")
            return True

        print("[ERROR] 로그인 실패")
        return False

    async def get_page_data(self, url: str) -> dict:
        """페이지에서 __NEXT_DATA__ 또는 window 데이터 추출"""
        await self.page.goto(url, wait_until="networkidle")
        await self.page.wait_for_timeout(2000)

        # Next.js __NEXT_DATA__ 추출
        next_data = await self.page.evaluate('''() => {
            const el = document.getElementById("__NEXT_DATA__");
            if (el) return JSON.parse(el.textContent);
            return null;
        }''')

        if next_data:
            return next_data

        # window 객체에서 데이터 추출
        window_data = await self.page.evaluate('''() => {
            const data = {};
            // 일반적인 데이터 키 확인
            const keys = ["__PRELOADED_STATE__", "__INITIAL_STATE__", "pageData", "initialData"];
            for (const key of keys) {
                if (window[key]) data[key] = window[key];
            }
            return data;
        }''')

        return window_data

    async def scrape_shows_page(self):
        """쇼 목록 페이지 스크래핑"""
        print("\n[INFO] 쇼 목록 스크래핑...")

        await self.page.goto(f"{self.BASE_URL}/shows", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 스크롤하여 모든 콘텐츠 로드
        for _ in range(5):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1000)

        # 쇼 카드 추출
        shows = await self.page.evaluate('''() => {
            const shows = [];
            // 링크에서 쇼 정보 추출
            document.querySelectorAll('a[href*="/shows/"]').forEach(link => {
                const href = link.getAttribute("href");
                if (href && href.includes("/shows/") && !href.endsWith("/shows/")) {
                    const slug = href.split("/shows/")[1]?.split("/")[0];
                    if (slug && !shows.find(s => s.slug === slug)) {
                        const title = link.textContent?.trim() ||
                                     link.querySelector("h2, h3, h4, [class*='title']")?.textContent?.trim() ||
                                     slug;
                        const img = link.querySelector("img")?.src;
                        shows.push({
                            slug: slug,
                            title: title,
                            url: "https://www.pokergo.com" + href,
                            thumbnail: img
                        });
                    }
                }
            });
            return shows;
        }''')

        print(f"  - {len(shows)}개 쇼 발견")
        self.collected_data["shows"] = shows
        return shows

    async def scrape_show_detail(self, show_url: str, show_slug: str):
        """개별 쇼 상세 페이지 스크래핑"""
        print(f"  - {show_slug} 스크래핑...")

        await self.page.goto(show_url, wait_until="networkidle")
        await self.page.wait_for_timeout(2000)

        # 시즌 정보 추출
        seasons = await self.page.evaluate('''() => {
            const seasons = [];
            document.querySelectorAll('a[href*="/seasons/"], [class*="season"]').forEach(el => {
                const href = el.getAttribute("href") || "";
                const text = el.textContent?.trim() || "";
                if (text || href) {
                    seasons.push({
                        text: text,
                        href: href
                    });
                }
            });
            return seasons;
        }''')

        # 에피소드/비디오 추출
        videos = await self.page.evaluate('''() => {
            const videos = [];
            document.querySelectorAll('a[href*="/videos/"], a[href*="/watch/"], [class*="episode"], [class*="video-card"]').forEach(el => {
                const href = el.getAttribute("href") || "";
                const title = el.querySelector("h2, h3, h4, [class*='title']")?.textContent?.trim() ||
                             el.textContent?.trim()?.substring(0, 100);
                const duration = el.querySelector("[class*='duration'], [class*='time']")?.textContent?.trim();
                const thumbnail = el.querySelector("img")?.src;

                if (href && (href.includes("/videos/") || href.includes("/watch/"))) {
                    videos.push({
                        title: title,
                        url: href.startsWith("http") ? href : "https://www.pokergo.com" + href,
                        duration: duration,
                        thumbnail: thumbnail
                    });
                }
            });
            return videos;
        }''')

        return {
            "seasons": seasons,
            "videos": videos
        }

    async def scrape_all_shows(self, max_shows: int = 50):
        """모든 쇼 상세 스크래핑"""
        shows = await self.scrape_shows_page()

        for i, show in enumerate(shows[:max_shows]):
            try:
                detail = await self.scrape_show_detail(show["url"], show["slug"])
                show["seasons"] = detail["seasons"]
                show["videos"] = detail["videos"]
                self.collected_data["videos"].extend([
                    {**v, "show": show["slug"], "show_title": show["title"]}
                    for v in detail["videos"]
                ])
                print(f"    → {len(detail['videos'])}개 비디오")
            except Exception as e:
                print(f"    → 오류: {e}")

            # 진행률
            if (i + 1) % 5 == 0:
                print(f"  [{i+1}/{min(len(shows), max_shows)}] 완료")

    async def scrape_featured_content(self):
        """홈페이지 주요 콘텐츠 스크래핑"""
        print("\n[INFO] 홈페이지 콘텐츠 스크래핑...")

        await self.page.goto(self.BASE_URL, wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 스크롤
        for _ in range(3):
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(1000)

        # 모든 비디오 링크 추출
        videos = await self.page.evaluate('''() => {
            const videos = [];
            document.querySelectorAll('a[href*="/videos/"], a[href*="/watch/"]').forEach(el => {
                const href = el.getAttribute("href");
                const title = el.querySelector("[class*='title'], h2, h3")?.textContent?.trim() ||
                             el.getAttribute("title") || "";
                const img = el.querySelector("img")?.src;

                if (href && !videos.find(v => v.url === href)) {
                    videos.push({
                        url: href.startsWith("http") ? href : "https://www.pokergo.com" + href,
                        title: title,
                        thumbnail: img,
                        source: "homepage"
                    });
                }
            });
            return videos;
        }''')

        print(f"  - {len(videos)}개 비디오 발견")
        return videos

    async def scrape_event_pages(self):
        """이벤트 페이지들 스크래핑"""
        print("\n[INFO] 이벤트 페이지 스크래핑...")

        event_paths = [
            "/wsop",
            "/wpt",
            "/high-stakes-poker",
            "/poker-after-dark",
            "/hustler-casino-live",
            "/super-high-roller-bowl",
        ]

        all_videos = []

        for path in event_paths:
            print(f"  - {path}")
            try:
                await self.page.goto(f"{self.BASE_URL}{path}", wait_until="networkidle")
                await self.page.wait_for_timeout(2000)

                # 스크롤
                for _ in range(3):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(800)

                videos = await self.page.evaluate('''(eventPath) => {
                    const videos = [];
                    document.querySelectorAll('a[href*="/videos/"], a[href*="/watch/"], a[href*="/seasons/"]').forEach(el => {
                        const href = el.getAttribute("href");
                        const title = el.querySelector("[class*='title'], h2, h3")?.textContent?.trim() ||
                                     el.textContent?.trim()?.substring(0, 100);
                        const img = el.querySelector("img")?.src;

                        if (href) {
                            videos.push({
                                url: href.startsWith("http") ? href : "https://www.pokergo.com" + href,
                                title: title,
                                thumbnail: img,
                                source: eventPath
                            });
                        }
                    });
                    return videos;
                }''', path)

                all_videos.extend(videos)
                print(f"    → {len(videos)}개 항목")

            except Exception as e:
                print(f"    → 오류: {e}")

        return all_videos

    def deduplicate_videos(self):
        """중복 비디오 제거"""
        seen = set()
        unique = []
        for v in self.collected_data["videos"]:
            url = v.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(v)
        self.collected_data["videos"] = unique

    def save_data(self):
        """데이터 저장"""
        self.collected_data["scraped_at"] = datetime.now().isoformat()
        self.deduplicate_videos()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 메인 데이터
        main_file = OUTPUT_DIR / f"pokergo_full_{timestamp}.json"
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

        # API 응답 (디버깅용)
        api_file = OUTPUT_DIR / f"pokergo_api_all_{timestamp}.json"
        with open(api_file, "w", encoding="utf-8") as f:
            json.dump(self.all_api_responses, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[SUCCESS] 스크래핑 완료!")
        print(f"{'='*60}")
        print(f"  메인 파일: {main_file}")
        print(f"  API 파일: {api_file}")
        print("\n[통계]")
        print(f"  - 쇼: {len(self.collected_data['shows'])}개")
        print(f"  - 비디오: {len(self.collected_data['videos'])}개")
        print(f"  - API 응답: {len(self.all_api_responses)}개")

        return main_file


async def main():
    print("=" * 60)
    print("PokerGO 전체 스크래퍼")
    print("=" * 60)

    scraper = PokerGoFullScraper(headless=False)

    try:
        await scraper.start()

        if not await scraper.login():
            print("[WARNING] 로그인 없이 진행")

        # 홈페이지 콘텐츠
        homepage_videos = await scraper.scrape_featured_content()
        scraper.collected_data["videos"].extend(homepage_videos)

        # 이벤트 페이지
        event_videos = await scraper.scrape_event_pages()
        scraper.collected_data["videos"].extend(event_videos)

        # 모든 쇼 스크래핑
        await scraper.scrape_all_shows(max_shows=100)

        # 저장
        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
