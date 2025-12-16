"""
PokerGO 비디오 상세 스크래퍼

기존에 수집된 비디오 URL을 순회하며 상세 메타데이터를 수집합니다.
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

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"
DATA_DIR.mkdir(parents=True, exist_ok=True)


class PokerGoDetailScraper:
    """PokerGO 비디오 상세 스크래퍼"""

    BASE_URL = "https://www.pokergo.com"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Browser | None = None
        self.page: Page | None = None
        self.videos_with_details: list = []
        self.failed_urls: list = []

    async def start(self):
        """브라우저 시작"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        self.page = await context.new_page()
        print("[INFO] 브라우저 시작")

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

    async def scrape_video_detail(self, video_url: str) -> dict | None:
        """개별 비디오 상세 페이지 스크래핑"""
        try:
            await self.page.goto(video_url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # 상세 정보 추출
            detail = await self.page.evaluate('''() => {
                const data = {
                    title: "",
                    description: "",
                    duration: "",
                    duration_seconds: 0,
                    show_name: "",
                    season: "",
                    episode: "",
                    air_date: "",
                    thumbnail: "",
                    tags: [],
                    event: ""
                };

                // 제목 추출 - og:title이 가장 정확함
                const ogTitle = document.querySelector('meta[property="og:title"]');
                if (ogTitle) {
                    data.title = ogTitle.getAttribute('content')?.replace(' | PokerGO', '').trim() || "";
                }
                if (!data.title) {
                    const h1 = document.querySelector('h1');
                    if (h1) {
                        data.title = h1.textContent?.trim() || "";
                    }
                }

                // 설명 추출 - og:description이 가장 정확함
                const ogDesc = document.querySelector('meta[property="og:description"]');
                if (ogDesc) {
                    data.description = ogDesc.getAttribute('content')?.trim() || "";
                }
                if (!data.description) {
                    const metaDesc = document.querySelector('meta[name="description"]');
                    if (metaDesc) {
                        data.description = metaDesc.getAttribute('content')?.trim() || "";
                    }
                }

                // 썸네일
                const ogImage = document.querySelector('meta[property="og:image"]');
                if (ogImage) {
                    data.thumbnail = ogImage.getAttribute('content');
                }

                // Duration - aria-label에서 추출 (가장 정확)
                const durationLabel = document.querySelector('[aria-label*="of"]');
                if (durationLabel) {
                    const label = durationLabel.getAttribute('aria-label') || "";
                    // "0 seconds of 3 hours, 20 minutes, 28 seconds" 형식 파싱
                    const match = label.match(/of\s+(?:(\d+)\s*hours?)?,?\s*(?:(\d+)\s*minutes?)?,?\s*(?:(\d+)\s*seconds?)?/i);
                    if (match) {
                        const hours = parseInt(match[1]) || 0;
                        const minutes = parseInt(match[2]) || 0;
                        const seconds = parseInt(match[3]) || 0;
                        data.duration_seconds = hours * 3600 + minutes * 60 + seconds;
                        if (hours > 0) {
                            data.duration = `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
                        } else {
                            data.duration = `${minutes}:${String(seconds).padStart(2, '0')}`;
                        }
                    }
                }

                // 시즌/에피소드 정보 - URL과 제목에서 추출
                const url = window.location.pathname;
                const title = data.title;

                // URL 패턴: s08, season-8 등
                const urlSeasonMatch = url.match(/[-_]s(\d+)[-_]|season[-_]?(\d+)/i);
                if (urlSeasonMatch) {
                    data.season = urlSeasonMatch[1] || urlSeasonMatch[2];
                }

                // 제목에서 "Season X" 추출
                const titleSeasonMatch = title.match(/Season\s*(\d+)/i);
                if (titleSeasonMatch && !data.season) {
                    data.season = titleSeasonMatch[1];
                }

                // 에피소드 - URL이나 제목에서 추출
                const urlEpMatch = url.match(/[-_]ep?(\d+)[-_]|episode[-_]?(\d+)/i);
                if (urlEpMatch) {
                    data.episode = urlEpMatch[1] || urlEpMatch[2];
                }
                const titleEpMatch = title.match(/Episode\s*(\d+)|Ep\.?\s*(\d+)/i);
                if (titleEpMatch && !data.episode) {
                    data.episode = titleEpMatch[1] || titleEpMatch[2];
                }

                // Day 정보도 에피소드로 사용
                if (!data.episode) {
                    const dayMatch = url.match(/day[-_]?(\d+)/i) || title.match(/Day\s*(\d+)/i);
                    if (dayMatch) {
                        data.episode = `Day ${dayMatch[1]}`;
                    }
                }

                // 쇼 이름 추출 - 제목의 첫 부분이나 브레드크럼에서
                const breadcrumb = document.querySelector('a[href*="/shows/"]');
                if (breadcrumb) {
                    data.show_name = breadcrumb.textContent?.trim() || "";
                }
                // 제목에서 쇼 이름 추출 (첫 | 이전 부분)
                if (!data.show_name && data.title.includes('|')) {
                    data.show_name = data.title.split('|')[0].trim();
                }

                // 이벤트/쇼 타입 추출
                const eventMap = {
                    'WSOP': ['WSOP', 'World Series of Poker'],
                    'WPT': ['WPT', 'World Poker Tour'],
                    'High Stakes Poker': ['High Stakes Poker', 'HSP'],
                    'Poker After Dark': ['Poker After Dark', 'PAD'],
                    'Super High Roller Bowl': ['Super High Roller Bowl', 'SHRB'],
                    'Hustler Casino Live': ['Hustler Casino Live', 'HCL'],
                    'No Gamble No Future': ['No Gamble No Future', 'NGNF'],
                    'PGT': ['PGT', 'PokerGO Tour']
                };

                for (const [event, keywords] of Object.entries(eventMap)) {
                    if (keywords.some(k => data.title.includes(k) || url.includes(k.toLowerCase().replace(/ /g, '-')))) {
                        data.event = event;
                        break;
                    }
                }

                return data;
            }''')

            return detail

        except Exception as e:
            print(f"    [ERROR] {video_url}: {e}")
            return None

    def load_existing_videos(self, input_file: str = None) -> list:
        """기존 수집된 비디오 목록 로드"""
        if input_file:
            file_path = Path(input_file)
        else:
            # 가장 최근 파일 찾기
            files = list(DATA_DIR.glob("pokergo_full_*.json"))
            if not files:
                print("[ERROR] 기존 데이터 파일이 없습니다")
                return []
            file_path = max(files, key=lambda f: f.stat().st_mtime)

        print(f"[INFO] 데이터 로드: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        videos = data.get("videos", [])
        print(f"  - {len(videos)}개 비디오 발견")
        return videos

    async def scrape_all_details(self, videos: list, max_videos: int = None, start_from: int = 0):
        """모든 비디오 상세 스크래핑"""
        total = len(videos)
        if max_videos:
            videos = videos[start_from:start_from + max_videos]
        else:
            videos = videos[start_from:]

        print(f"\n[INFO] {len(videos)}개 비디오 상세 스크래핑 시작 (전체: {total})")

        for i, video in enumerate(videos):
            url = video.get("url", "")
            if not url:
                continue

            print(f"  [{i+1}/{len(videos)}] {url.split('/')[-1][:50]}...")

            detail = await self.scrape_video_detail(url)

            if detail:
                # 기존 정보와 병합
                enriched = {
                    **video,
                    **{k: v for k, v in detail.items() if v},  # 빈 값 제외
                }
                # 기존에 title이 없거나 빈 경우에만 새 title 사용
                if not video.get("title") and detail.get("title"):
                    enriched["title"] = detail["title"]
                elif video.get("title"):
                    enriched["title"] = video["title"]

                self.videos_with_details.append(enriched)
            else:
                self.failed_urls.append(url)
                # 실패해도 기존 정보는 유지
                self.videos_with_details.append(video)

            # 진행 상황 출력
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(videos)}] 완료 - 성공: {len(self.videos_with_details) - len(self.failed_urls)}, 실패: {len(self.failed_urls)}")

            # 속도 조절
            await asyncio.sleep(1)

        print("\n[INFO] 스크래핑 완료")
        print(f"  - 성공: {len(self.videos_with_details) - len(self.failed_urls)}개")
        print(f"  - 실패: {len(self.failed_urls)}개")

    def save_data(self):
        """데이터 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 상세 데이터 저장
        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(self.videos_with_details),
            "failed_count": len(self.failed_urls),
            "videos": self.videos_with_details,
            "failed_urls": self.failed_urls
        }

        output_file = DATA_DIR / f"pokergo_details_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[SUCCESS] 저장 완료!")
        print(f"{'='*60}")
        print(f"  파일: {output_file}")
        print(f"  비디오 수: {len(self.videos_with_details)}개")

        # 통계 출력
        titles_count = sum(1 for v in self.videos_with_details if v.get("title"))
        desc_count = sum(1 for v in self.videos_with_details if v.get("description"))
        show_count = sum(1 for v in self.videos_with_details if v.get("show_name"))

        print("\n[통계]")
        print(f"  - 제목 있음: {titles_count}개")
        print(f"  - 설명 있음: {desc_count}개")
        print(f"  - 쇼 정보 있음: {show_count}개")

        return output_file


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='PokerGO 비디오 상세 스크래퍼')
    parser.add_argument('--max', type=int, default=None, help='최대 스크래핑 수')
    parser.add_argument('--start', type=int, default=0, help='시작 인덱스')
    parser.add_argument('--input', type=str, default=None, help='입력 파일 경로')
    parser.add_argument('--headless', action='store_true', help='헤드리스 모드')
    args = parser.parse_args()

    print("=" * 60)
    print("PokerGO 비디오 상세 스크래퍼")
    print("=" * 60)

    scraper = PokerGoDetailScraper(headless=args.headless)

    try:
        # 기존 데이터 로드
        videos = scraper.load_existing_videos(args.input)
        if not videos:
            print("[ERROR] 비디오 목록이 없습니다. 먼저 pokergo_full_scraper.py를 실행하세요.")
            return

        await scraper.start()

        if not await scraper.login():
            print("[WARNING] 로그인 없이 진행 (일부 콘텐츠 제한될 수 있음)")

        await scraper.scrape_all_details(
            videos,
            max_videos=args.max,
            start_from=args.start
        )

        scraper.save_data()

    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
