"""
PokerGO 페이지 구조 디버깅
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo" / "debug"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    print("=" * 60)
    print("PokerGO Debug - Page Structure Analysis")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    # API 응답 캡처
    api_responses = []

    async def capture_response(response):
        url = response.url
        if "api" in url.lower() or "graphql" in url.lower():
            try:
                if response.status == 200:
                    content_type = response.headers.get("content-type", "")
                    if "json" in content_type:
                        data = await response.json()
                        api_responses.append({"url": url, "data": data})
                        print(f"  [API] {url[:80]}...")
            except Exception:
                pass

    page.on("response", capture_response)

    try:
        # 로그인
        print("\n[1] Logging in...")
        await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        email_input = await page.query_selector('input[type="email"], input[name="email"]')
        if email_input:
            await email_input.fill(POKERGO_ID)

        pwd_input = await page.query_selector('input[type="password"]')
        if pwd_input:
            await pwd_input.fill(POKERGO_PASSWORD)

        login_btn = await page.query_selector('button[type="submit"], button:has-text("Log")')
        if login_btn:
            await login_btn.click()
            await page.wait_for_timeout(5000)

        print(f"  Current URL: {page.url}")

        # WSOP 페이지로 이동
        print("\n[2] Going to WSOP page...")
        await page.goto("https://www.pokergo.com/wsop", wait_until="networkidle")
        await page.wait_for_timeout(5000)

        # 스크롤
        print("\n[3] Scrolling...")
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            print(f"  Scroll {i+1}/5")

        # 스크린샷 저장
        print("\n[4] Saving screenshot...")
        screenshot_path = OUTPUT_DIR / "wsop_page.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  Saved: {screenshot_path}")

        # HTML 저장
        print("\n[5] Saving HTML...")
        html_content = await page.content()
        html_path = OUTPUT_DIR / "wsop_page.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"  Saved: {html_path}")
        print(f"  HTML size: {len(html_content):,} bytes")

        # 링크 분석
        print("\n[6] Analyzing links...")
        all_links = await page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('a').forEach(a => {
                links.push({
                    href: a.getAttribute('href'),
                    text: a.textContent?.trim()?.substring(0, 50),
                    classes: a.className
                });
            });
            return links;
        }''')

        print(f"  Total links: {len(all_links)}")

        # 비디오 관련 링크
        video_links = [lnk for lnk in all_links if lnk['href'] and ('video' in lnk['href'].lower() or 'watch' in lnk['href'].lower())]
        print(f"  Video links: {len(video_links)}")

        if video_links:
            print("\n  Sample video links:")
            for link in video_links[:10]:
                print(f"    - {link['href']} | {link['text']}")

        # API 응답 저장
        if api_responses:
            print(f"\n[7] API responses captured: {len(api_responses)}")
            import json
            api_path = OUTPUT_DIR / "wsop_api_responses.json"
            with open(api_path, "w", encoding="utf-8") as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=2)
            print(f"  Saved: {api_path}")

        # 페이지 요소 분석
        print("\n[8] Analyzing page elements...")
        elements = await page.evaluate('''() => {
            return {
                divs: document.querySelectorAll('div').length,
                imgs: document.querySelectorAll('img').length,
                buttons: document.querySelectorAll('button').length,
                iframes: document.querySelectorAll('iframe').length,
                shadowRoots: document.querySelectorAll('*').length,
            };
        }''')
        print(f"  Elements: {elements}")

        print("\n" + "=" * 60)
        print("Debug files saved to:", OUTPUT_DIR)
        print("=" * 60)

    finally:
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
