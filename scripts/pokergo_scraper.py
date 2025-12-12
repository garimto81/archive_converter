"""
PokerGO 웹 스크래퍼

로그인 후 비디오 메타데이터를 수집합니다.
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


class PokerGoScraper:
    """PokerGO 스크래퍼"""

    BASE_URL = "https://www.pokergo.com"
    LOGIN_URL = "https://www.pokergo.com/login"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.collected_data: dict = {
            "scraped_at": None,
            "shows": [],
            "videos": [],
            "events": [],
        }

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        print(f"[INFO] 브라우저 시작 (headless={self.headless})")

    async def close(self):
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            print("[INFO] 브라우저 종료")

    async def login(self) -> bool:
        """PokerGO 로그인"""
        if not POKERGO_ID or not POKERGO_PASSWORD:
            print("[ERROR] POKERGO_ID 또는 POKERGO_PASSWORD가 설정되지 않았습니다.")
            return False

        print(f"[INFO] 로그인 시도: {POKERGO_ID}")

        try:
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 이메일 입력
            email_input = await self.page.query_selector('input[type="email"], input[name="email"], input[placeholder*="email" i]')
            if email_input:
                await email_input.fill(POKERGO_ID)
            else:
                # 대체 선택자 시도
                await self.page.fill('input[type="text"]', POKERGO_ID)

            # 비밀번호 입력
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(POKERGO_PASSWORD)

            # 로그인 버튼 클릭
            login_button = await self.page.query_selector('button[type="submit"], button:has-text("Sign In"), button:has-text("Log In")')
            if login_button:
                await login_button.click()
            else:
                await self.page.press('input[type="password"]', "Enter")

            # 로그인 완료 대기
            await self.page.wait_for_timeout(3000)

            # 로그인 성공 확인
            current_url = self.page.url
            if "login" not in current_url.lower():
                print("[SUCCESS] 로그인 성공!")
                return True
            else:
                print("[ERROR] 로그인 실패 - 여전히 로그인 페이지에 있음")
                return False

        except Exception as e:
            print(f"[ERROR] 로그인 중 오류: {e}")
            return False

    async def scrape_shows(self):
        """모든 쇼/시리즈 목록 수집"""
        print("[INFO] 쇼 목록 수집 중...")

        try:
            # 메인 페이지에서 쇼 목록 찾기
            await self.page.goto(f"{self.BASE_URL}/shows", wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 쇼 카드들 찾기
            show_cards = await self.page.query_selector_all('[class*="show"], [class*="card"], [class*="series"], a[href*="/shows/"]')

            for card in show_cards:
                try:
                    title = await card.inner_text()
                    href = await card.get_attribute("href")

                    if href and "/shows/" in href:
                        show_data = {
                            "title": title.strip() if title else "",
                            "url": href if href.startswith("http") else f"{self.BASE_URL}{href}",
                            "slug": href.split("/shows/")[-1].split("/")[0] if "/shows/" in href else "",
                        }
                        if show_data["slug"] and show_data not in self.collected_data["shows"]:
                            self.collected_data["shows"].append(show_data)
                            print(f"  - {show_data['title'] or show_data['slug']}")
                except Exception:
                    continue

            print(f"[INFO] 총 {len(self.collected_data['shows'])}개 쇼 발견")

        except Exception as e:
            print(f"[ERROR] 쇼 목록 수집 오류: {e}")

    async def scrape_events(self):
        """이벤트 목록 수집 (WSOP, WPT 등)"""
        print("[INFO] 이벤트 목록 수집 중...")

        event_pages = [
            "/events",
            "/wsop",
            "/wpt",
            "/high-stakes-poker",
            "/poker-after-dark",
        ]

        for event_path in event_pages:
            try:
                await self.page.goto(f"{self.BASE_URL}{event_path}", wait_until="networkidle")
                await self.page.wait_for_timeout(1500)

                # 이벤트 정보 추출
                title = await self.page.title()

                # 비디오 링크 찾기
                video_links = await self.page.query_selector_all('a[href*="/videos/"], a[href*="/watch/"]')

                event_data = {
                    "path": event_path,
                    "title": title,
                    "video_count": len(video_links),
                }
                self.collected_data["events"].append(event_data)
                print(f"  - {event_path}: {title} ({len(video_links)} videos)")

            except Exception as e:
                print(f"  - {event_path}: 오류 - {e}")

    async def scrape_videos_from_page(self, url: str) -> list:
        """특정 페이지에서 비디오 정보 추출"""
        videos = []

        try:
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 비디오 카드/항목 찾기
            video_elements = await self.page.query_selector_all(
                '[class*="video"], [class*="episode"], [class*="card"], '
                'a[href*="/videos/"], a[href*="/watch/"]'
            )

            for elem in video_elements:
                try:
                    video_data = {}

                    # 링크
                    href = await elem.get_attribute("href")
                    if href:
                        video_data["url"] = href if href.startswith("http") else f"{self.BASE_URL}{href}"

                    # 제목
                    title_elem = await elem.query_selector('[class*="title"], h2, h3, h4')
                    if title_elem:
                        video_data["title"] = (await title_elem.inner_text()).strip()

                    # 설명
                    desc_elem = await elem.query_selector('[class*="description"], [class*="desc"], p')
                    if desc_elem:
                        video_data["description"] = (await desc_elem.inner_text()).strip()

                    # 날짜
                    date_elem = await elem.query_selector('[class*="date"], time')
                    if date_elem:
                        video_data["date"] = (await date_elem.inner_text()).strip()

                    # Duration
                    duration_elem = await elem.query_selector('[class*="duration"], [class*="time"]')
                    if duration_elem:
                        video_data["duration"] = (await duration_elem.inner_text()).strip()

                    if video_data.get("url") or video_data.get("title"):
                        videos.append(video_data)

                except Exception:
                    continue

        except Exception as e:
            print(f"[ERROR] 비디오 추출 오류 ({url}): {e}")

        return videos

    async def scrape_all_videos(self, max_pages: int = 10):
        """모든 비디오 수집"""
        print("[INFO] 비디오 목록 수집 중...")

        # 각 쇼에서 비디오 수집
        for show in self.collected_data["shows"][:max_pages]:
            show_url = show.get("url", "")
            if show_url:
                print(f"  - {show.get('title', show.get('slug', 'Unknown'))} 스캔 중...")
                videos = await self.scrape_videos_from_page(show_url)
                for v in videos:
                    v["show"] = show.get("title", show.get("slug", ""))
                    if v not in self.collected_data["videos"]:
                        self.collected_data["videos"].append(v)

        print(f"[INFO] 총 {len(self.collected_data['videos'])}개 비디오 발견")

    async def scrape_video_details(self, video_url: str) -> dict:
        """개별 비디오 상세 정보 수집"""
        details = {}

        try:
            await self.page.goto(video_url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 제목
            title = await self.page.query_selector('h1, [class*="title"]')
            if title:
                details["title"] = (await title.inner_text()).strip()

            # 설명
            desc = await self.page.query_selector('[class*="description"], [class*="synopsis"]')
            if desc:
                details["description"] = (await desc.inner_text()).strip()

            # 메타 정보 (시즌, 에피소드 등)
            meta_elements = await self.page.query_selector_all('[class*="meta"], [class*="info"]')
            for meta in meta_elements:
                text = await meta.inner_text()
                details["meta"] = details.get("meta", [])
                details["meta"].append(text.strip())

            # 태그
            tags = await self.page.query_selector_all('[class*="tag"], [class*="category"]')
            details["tags"] = []
            for tag in tags:
                details["tags"].append((await tag.inner_text()).strip())

            details["url"] = video_url

        except Exception as e:
            print(f"[ERROR] 비디오 상세 정보 오류: {e}")

        return details

    async def intercept_api_calls(self):
        """API 호출 감지 및 수집"""
        api_responses = []

        async def handle_response(response):
            url = response.url
            if "api" in url.lower() or "graphql" in url.lower():
                try:
                    if "application/json" in response.headers.get("content-type", ""):
                        data = await response.json()
                        api_responses.append({
                            "url": url,
                            "data": data,
                        })
                        print(f"[API] {url[:80]}...")
                except Exception:
                    pass

        self.page.on("response", handle_response)
        return api_responses

    def save_data(self):
        """수집된 데이터 저장"""
        self.collected_data["scraped_at"] = datetime.now().isoformat()

        output_file = OUTPUT_DIR / f"pokergo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.collected_data, f, ensure_ascii=False, indent=2)

        print(f"[SUCCESS] 데이터 저장됨: {output_file}")
        print(f"  - 쇼: {len(self.collected_data['shows'])}개")
        print(f"  - 비디오: {len(self.collected_data['videos'])}개")
        print(f"  - 이벤트: {len(self.collected_data['events'])}개")

        return output_file


async def main():
    """메인 실행"""
    print("=" * 60)
    print("PokerGO 스크래퍼 시작")
    print("=" * 60)

    scraper = PokerGoScraper(headless=False)  # headless=True로 변경 가능

    try:
        await scraper.start()

        # API 호출 감지 시작
        api_data = await scraper.intercept_api_calls()

        # 로그인
        if not await scraper.login():
            print("[ERROR] 로그인 실패로 종료합니다.")
            return

        # 데이터 수집
        await scraper.scrape_shows()
        await scraper.scrape_events()
        await scraper.scrape_all_videos(max_pages=20)

        # API 데이터 추가
        if api_data:
            scraper.collected_data["api_responses"] = api_data

        # 저장
        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
