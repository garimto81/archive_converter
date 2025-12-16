"""
PokerGO API 스크래퍼

API를 직접 호출하여 비디오 메타데이터를 수집합니다.
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


class PokerGoApiScraper:
    """PokerGO API 스크래퍼"""

    BASE_URL = "https://www.pokergo.com"
    API_BASE = "https://api.pokergo.com/v4/api"
    LOGIN_URL = "https://www.pokergo.com/login"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.auth_token: str | None = None
        self.api_responses: list = []
        self.collected_data: dict = {
            "scraped_at": None,
            "shows": [],
            "videos": [],
            "events": [],
            "collections": [],
            "categories": [],
        }

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()

        # API 응답 캡처
        self.page.on("response", self._capture_api_response)

        print(f"[INFO] 브라우저 시작 (headless={self.headless})")

    async def _capture_api_response(self, response):
        """API 응답 캡처"""
        url = response.url
        if "api.pokergo.com" in url:
            try:
                content_type = response.headers.get("content-type", "")
                if "application/json" in content_type:
                    data = await response.json()
                    self.api_responses.append({
                        "url": url,
                        "status": response.status,
                        "data": data,
                    })

                    # 토큰 추출
                    if "token" in str(data).lower():
                        if isinstance(data, dict):
                            if "token" in data:
                                self.auth_token = data["token"]
                            elif "data" in data and isinstance(data["data"], dict):
                                if "token" in data["data"]:
                                    self.auth_token = data["data"]["token"]

            except Exception:
                pass

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
            await self.page.wait_for_timeout(3000)

            # 스크린샷 저장 (디버깅용)
            await self.page.screenshot(path=str(OUTPUT_DIR / "login_page.png"))

            # 이메일 입력 필드 찾기
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email" i]',
                'input[placeholder*="Email" i]',
                '#email',
                'input[autocomplete="email"]',
            ]

            email_input = None
            for selector in email_selectors:
                email_input = await self.page.query_selector(selector)
                if email_input:
                    break

            if email_input:
                await email_input.fill(POKERGO_ID)
                print("[INFO] 이메일 입력 완료")
            else:
                # 모든 input 필드 찾기
                inputs = await self.page.query_selector_all('input')
                print(f"[DEBUG] 발견된 input 필드: {len(inputs)}개")
                for i, inp in enumerate(inputs):
                    inp_type = await inp.get_attribute("type")
                    inp_name = await inp.get_attribute("name")
                    inp_placeholder = await inp.get_attribute("placeholder")
                    print(f"  [{i}] type={inp_type}, name={inp_name}, placeholder={inp_placeholder}")

                # 첫 번째 텍스트/이메일 필드에 입력 시도
                for inp in inputs:
                    inp_type = await inp.get_attribute("type")
                    if inp_type in ["text", "email", None]:
                        await inp.fill(POKERGO_ID)
                        print("[INFO] 첫 번째 입력 필드에 이메일 입력")
                        break

            await self.page.wait_for_timeout(500)

            # 비밀번호 입력
            password_input = await self.page.query_selector('input[type="password"]')
            if password_input:
                await password_input.fill(POKERGO_PASSWORD)
                print("[INFO] 비밀번호 입력 완료")

            await self.page.wait_for_timeout(500)

            # 로그인 버튼 클릭
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")',
                'button:has-text("LOGIN")',
                'input[type="submit"]',
            ]

            clicked = False
            for selector in button_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        await button.click()
                        clicked = True
                        print(f"[INFO] 로그인 버튼 클릭: {selector}")
                        break
                except Exception:
                    continue

            if not clicked:
                await self.page.press('input[type="password"]', "Enter")
                print("[INFO] Enter 키로 로그인 시도")

            # 로그인 완료 대기
            await self.page.wait_for_timeout(5000)

            # 로그인 후 스크린샷
            await self.page.screenshot(path=str(OUTPUT_DIR / "after_login.png"))

            # 로그인 성공 확인
            current_url = self.page.url
            print(f"[INFO] 현재 URL: {current_url}")

            if "login" not in current_url.lower():
                print("[SUCCESS] 로그인 성공!")
                return True
            else:
                print("[ERROR] 로그인 실패 - 여전히 로그인 페이지에 있음")
                return False

        except Exception as e:
            print(f"[ERROR] 로그인 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def navigate_and_capture(self, path: str, name: str):
        """페이지 이동 및 API 응답 캡처"""
        print(f"[INFO] {name} 페이지 스캔: {path}")

        before_count = len(self.api_responses)

        try:
            await self.page.goto(f"{self.BASE_URL}{path}", wait_until="networkidle")
            await self.page.wait_for_timeout(3000)

            # 스크롤하여 더 많은 콘텐츠 로드
            for _ in range(3):
                await self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                await self.page.wait_for_timeout(1000)

            new_responses = len(self.api_responses) - before_count
            print(f"  - {new_responses}개 API 응답 캡처됨")

        except Exception as e:
            print(f"  - 오류: {e}")

    async def scrape_all_pages(self):
        """모든 주요 페이지 스캔"""
        pages = [
            ("/", "홈"),
            ("/shows", "쇼 목록"),
            ("/collections", "컬렉션"),
            ("/events", "이벤트"),
            ("/live", "라이브"),
            ("/wsop", "WSOP"),
            ("/wpt", "WPT"),
            ("/high-stakes-poker", "High Stakes Poker"),
            ("/poker-after-dark", "Poker After Dark"),
            ("/hustler-casino-live", "Hustler Casino Live"),
            ("/super-high-roller-bowl", "Super High Roller Bowl"),
            ("/pokergo-tour", "PokerGO Tour"),
        ]

        for path, name in pages:
            await self.navigate_and_capture(path, name)

    def process_api_responses(self):
        """캡처된 API 응답 처리"""
        print(f"\n[INFO] API 응답 처리 중... (총 {len(self.api_responses)}개)")

        for resp in self.api_responses:
            url = resp["url"]
            data = resp["data"]

            try:
                # 쇼/시리즈 데이터
                if "/shows" in url or "/series" in url:
                    self._extract_shows(data)

                # 비디오 데이터
                if "/videos" in url or "/episodes" in url or "/content" in url:
                    self._extract_videos(data)

                # 컬렉션 데이터
                if "/collections" in url:
                    self._extract_collections(data)

                # 이벤트 데이터
                if "/events" in url:
                    self._extract_events(data)

                # 카테고리 데이터
                if "/categories" in url or "/genres" in url:
                    self._extract_categories(data)

                # 일반 데이터 추출
                self._extract_any_content(data)

            except Exception as e:
                print(f"  - 처리 오류 ({url}): {e}")

    def _extract_shows(self, data):
        """쇼 데이터 추출"""
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]

            if isinstance(data, list):
                for item in data:
                    show = self._extract_item(item, "show")
                    if show and show not in self.collected_data["shows"]:
                        self.collected_data["shows"].append(show)

    def _extract_videos(self, data):
        """비디오 데이터 추출"""
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]

            if isinstance(data, list):
                for item in data:
                    video = self._extract_item(item, "video")
                    if video and video not in self.collected_data["videos"]:
                        self.collected_data["videos"].append(video)

    def _extract_collections(self, data):
        """컬렉션 데이터 추출"""
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]

            if isinstance(data, list):
                for item in data:
                    collection = self._extract_item(item, "collection")
                    if collection and collection not in self.collected_data["collections"]:
                        self.collected_data["collections"].append(collection)

    def _extract_events(self, data):
        """이벤트 데이터 추출"""
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]

            if isinstance(data, list):
                for item in data:
                    event = self._extract_item(item, "event")
                    if event and event not in self.collected_data["events"]:
                        self.collected_data["events"].append(event)

    def _extract_categories(self, data):
        """카테고리 데이터 추출"""
        if isinstance(data, dict):
            if "data" in data:
                data = data["data"]

            if isinstance(data, list):
                for item in data:
                    category = self._extract_item(item, "category")
                    if category and category not in self.collected_data["categories"]:
                        self.collected_data["categories"].append(category)

    def _extract_any_content(self, data):
        """일반 콘텐츠 데이터 추출"""
        if isinstance(data, dict):
            # rows, items, results 등의 키에서 데이터 추출
            for key in ["rows", "items", "results", "content", "entries"]:
                if key in data and isinstance(data[key], list):
                    for item in data[key]:
                        if isinstance(item, dict):
                            # 아이템 타입 추론
                            item_type = item.get("type", item.get("content_type", "unknown"))

                            if "video" in str(item_type).lower() or "episode" in str(item_type).lower():
                                video = self._extract_item(item, "video")
                                if video and video not in self.collected_data["videos"]:
                                    self.collected_data["videos"].append(video)
                            elif "show" in str(item_type).lower() or "series" in str(item_type).lower():
                                show = self._extract_item(item, "show")
                                if show and show not in self.collected_data["shows"]:
                                    self.collected_data["shows"].append(show)

    def _extract_item(self, item: dict, item_type: str) -> dict | None:
        """개별 아이템 데이터 추출"""
        if not isinstance(item, dict):
            return None

        extracted = {
            "type": item_type,
            "id": item.get("id") or item.get("uuid") or item.get("_id"),
            "title": item.get("title") or item.get("name"),
            "description": item.get("description") or item.get("synopsis") or item.get("summary"),
            "slug": item.get("slug") or item.get("permalink"),
            "thumbnail": item.get("thumbnail") or item.get("image") or item.get("poster"),
            "duration": item.get("duration") or item.get("runtime"),
            "published_at": item.get("published_at") or item.get("release_date") or item.get("air_date"),
            "season": item.get("season") or item.get("season_number"),
            "episode": item.get("episode") or item.get("episode_number"),
            "tags": item.get("tags") or item.get("genres") or [],
            "raw": item,  # 원본 데이터 보존
        }

        # None 값 제거
        extracted = {k: v for k, v in extracted.items() if v is not None}

        if extracted.get("id") or extracted.get("title"):
            return extracted
        return None

    def save_data(self):
        """수집된 데이터 저장"""
        self.collected_data["scraped_at"] = datetime.now().isoformat()

        # 메인 데이터 파일
        output_file = OUTPUT_DIR / f"pokergo_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # raw 데이터 제거하여 파일 크기 줄이기
        clean_data = json.loads(json.dumps(self.collected_data))
        for category in ["shows", "videos", "events", "collections", "categories"]:
            for item in clean_data.get(category, []):
                if "raw" in item:
                    del item["raw"]

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(clean_data, f, ensure_ascii=False, indent=2)

        # API 응답 전체 저장 (디버깅용)
        api_file = OUTPUT_DIR / f"pokergo_api_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(api_file, "w", encoding="utf-8") as f:
            json.dump(self.api_responses, f, ensure_ascii=False, indent=2)

        print("\n[SUCCESS] 데이터 저장 완료!")
        print(f"  - 메인 파일: {output_file}")
        print(f"  - API 응답: {api_file}")
        print("\n[통계]")
        print(f"  - 쇼: {len(self.collected_data['shows'])}개")
        print(f"  - 비디오: {len(self.collected_data['videos'])}개")
        print(f"  - 이벤트: {len(self.collected_data['events'])}개")
        print(f"  - 컬렉션: {len(self.collected_data['collections'])}개")
        print(f"  - 카테고리: {len(self.collected_data['categories'])}개")
        print(f"  - API 응답: {len(self.api_responses)}개")

        return output_file


async def main():
    """메인 실행"""
    print("=" * 60)
    print("PokerGO API 스크래퍼")
    print("=" * 60)

    scraper = PokerGoApiScraper(headless=False)

    try:
        await scraper.start()

        # 로그인
        if not await scraper.login():
            print("[WARNING] 로그인 없이 진행합니다 (일부 데이터만 수집 가능)")

        # 모든 페이지 스캔
        await scraper.scrape_all_pages()

        # API 응답 처리
        scraper.process_api_responses()

        # 저장
        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
