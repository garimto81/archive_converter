"""
PokerGO 영상 다운로드 테스트

1. 로그인하여 쿠키 저장
2. yt-dlp로 영상 다운로드 시도
3. 또는 HLS 스트림 URL 직접 추출
"""

import asyncio
import json
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo" / "downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COOKIES_FILE = OUTPUT_DIR / "pokergo_cookies.txt"


class PokerGoDownloader:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.video_urls = []

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await self.context.new_page()

        # 네트워크 요청 캡처 (HLS 스트림 찾기)
        self.page.on("response", self._capture_video_urls)

        print("[INFO] Browser started")

    async def _capture_video_urls(self, response):
        """비디오 스트림 URL 캡처"""
        url = response.url

        # HLS, DASH, MP4 등 비디오 URL 패턴
        video_patterns = [".m3u8", ".mpd", ".mp4", "manifest", "playlist", "stream", "video"]

        if any(p in url.lower() for p in video_patterns):
            if response.status == 200:
                content_type = response.headers.get("content-type", "")
                if "video" in content_type or "mpegurl" in content_type or "dash" in content_type or url.endswith(".m3u8"):
                    self.video_urls.append({
                        "url": url,
                        "content_type": content_type,
                        "status": response.status
                    })
                    print(f"  [VIDEO] {url[:100]}...")

    async def login(self):
        """PokerGO 로그인"""
        print(f"\n[INFO] Logging in as {POKERGO_ID}...")

        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await self.page.wait_for_timeout(3000)

        # 로그인 폼 입력
        try:
            # email input: name="email", placeholder="Email Address"
            email_input = await self.page.query_selector('input[name="email"]')
            if email_input:
                await email_input.fill(POKERGO_ID)
                print("  [OK] Email filled")
            else:
                print("  [WARN] Email input not found")

            # password input: type="password", placeholder="Password"
            pwd_input = await self.page.query_selector('input[type="password"]')
            if pwd_input:
                await pwd_input.fill(POKERGO_PASSWORD)
                print("  [OK] Password filled")
            else:
                print("  [WARN] Password input not found")

            await self.page.wait_for_timeout(1000)

            # login button: button with text "Login"
            login_btn = await self.page.query_selector('button:has-text("Login")')
            if login_btn:
                await login_btn.click()
                print("  [OK] Login button clicked")
            else:
                print("  [WARN] Login button not found")

            await self.page.wait_for_timeout(5000)

            current_url = self.page.url
            print(f"  [INFO] Current URL: {current_url}")

            if "login" not in current_url.lower():
                print("[OK] Login successful!")
                return True

        except Exception as e:
            print(f"[ERROR] Login failed: {e}")

        print("[WARN] Login may have failed")
        return False

    async def save_cookies(self):
        """쿠키를 Netscape 형식으로 저장 (yt-dlp 호환)"""
        cookies = await self.context.cookies()

        with open(COOKIES_FILE, "w") as f:
            f.write("# Netscape HTTP Cookie File\n")
            f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
            f.write("# This is a generated file! Do not edit.\n\n")

            for cookie in cookies:
                domain = cookie.get("domain", "")
                # 도메인이 .으로 시작하면 TRUE, 아니면 FALSE
                flag = "TRUE" if domain.startswith(".") else "FALSE"
                path = cookie.get("path", "/")
                secure = "TRUE" if cookie.get("secure", False) else "FALSE"
                expires = str(int(cookie.get("expires", 0)))
                name = cookie.get("name", "")
                value = cookie.get("value", "")

                f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

        print(f"[OK] Cookies saved: {COOKIES_FILE}")

    async def get_video_page(self, video_url: str):
        """비디오 페이지 방문하여 스트림 URL 수집"""
        print(f"\n[INFO] Opening video: {video_url}")

        self.video_urls.clear()

        await self.page.goto(video_url, wait_until="networkidle")
        await self.page.wait_for_timeout(5000)

        # 비디오 플레이어 찾기 및 재생 시도
        try:
            # 재생 버튼 클릭 시도
            play_btn = await self.page.query_selector('[class*="play"], button[aria-label*="play"], video')
            if play_btn:
                await play_btn.click()
                await self.page.wait_for_timeout(5000)
        except Exception:
            pass

        # 키보드로 재생 시도
        try:
            await self.page.keyboard.press("Space")
            await self.page.wait_for_timeout(3000)
        except Exception:
            pass

        print(f"[INFO] Captured {len(self.video_urls)} video URLs")
        return self.video_urls

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")


def download_with_ytdlp(video_url: str, cookies_file: Path, output_dir: Path):
    """yt-dlp로 다운로드 시도 (PokerGo extractor 사용)"""
    print("\n[INFO] Attempting download with yt-dlp...")
    print(f"  URL: {video_url}")

    output_template = str(output_dir / "%(title)s.%(ext)s")

    # PokerGo extractor는 --username/--password 사용
    cmd = [
        "yt-dlp",
        "--username", POKERGO_ID,
        "--password", POKERGO_PASSWORD,
        "-o", output_template,
        "--no-check-certificate",
        "-v",  # verbose
        video_url
    ]

    print("  Command: yt-dlp --username *** --password *** ...")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(f"\n[STDOUT]\n{result.stdout[:2000]}")
        if result.stderr:
            print(f"\n[STDERR]\n{result.stderr[:2000]}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("[ERROR] Download timeout")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


def download_hls_stream(m3u8_url: str, output_file: Path):
    """HLS 스트림 직접 다운로드"""
    print("\n[INFO] Downloading HLS stream...")
    print(f"  M3U8: {m3u8_url[:100]}...")

    cmd = [
        "yt-dlp",
        "--no-check-certificate",
        "-o", str(output_file),
        m3u8_url
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(f"[STDOUT] {result.stdout[:1000]}")
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def main():
    print("=" * 60)
    print("PokerGO Video Download Test")
    print("=" * 60)

    downloader = PokerGoDownloader()

    try:
        await downloader.start()

        # 로그인
        if await downloader.login():
            # 쿠키 저장
            await downloader.save_cookies()

            # 테스트할 비디오 URL (기존 스크래핑 데이터에서 하나 선택)
            test_video_url = "https://www.pokergo.com/videos/wsop-2018-main-event-episode-1"

            # 비디오 페이지 방문하여 스트림 URL 수집
            video_urls = await downloader.get_video_page(test_video_url)

            # 수집된 URL 저장
            if video_urls:
                urls_file = OUTPUT_DIR / "captured_urls.json"
                with open(urls_file, "w") as f:
                    json.dump(video_urls, f, indent=2)
                print(f"\n[OK] Video URLs saved: {urls_file}")

                # HLS 스트림 다운로드 시도
                for url_info in video_urls:
                    if ".m3u8" in url_info["url"]:
                        output_file = OUTPUT_DIR / "test_video.mp4"
                        download_hls_stream(url_info["url"], output_file)
                        break

            # yt-dlp 직접 다운로드 시도
            print("\n" + "=" * 60)
            print("Attempting yt-dlp direct download...")
            print("=" * 60)
            download_with_ytdlp(test_video_url, COOKIES_FILE, OUTPUT_DIR)

    finally:
        await downloader.close()


if __name__ == "__main__":
    asyncio.run(main())
