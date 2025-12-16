"""
WSOP 페이지 디버깅 - DOM 구조 분석
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv(Path(__file__).parent.parent / ".env")

POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"


async def main():
    print("=" * 60)
    print("WSOP Page Debug")
    print("=" * 60)

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    # Login
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[type="email"], input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("LOGIN"), button[type="submit"]')
    await page.wait_for_timeout(5000)
    print("[SUCCESS] Login!")

    # WSOP 2024 페이지
    print("\n[INFO] Going to WSOP 2024...")
    await page.goto("https://www.pokergo.com/collections/wsop-2024", wait_until="networkidle")
    await page.wait_for_timeout(5000)

    # 모든 링크 분석
    print("\n[DEBUG] Analyzing all links...")

    links = await page.evaluate('''() => {
        const result = [];
        document.querySelectorAll('a').forEach(a => {
            result.push({
                href: a.href || '',
                text: (a.innerText || '').trim().substring(0, 80),
                classStr: String(a.className || '').substring(0, 50)
            });
        });
        return result;
    }''')

    print(f"\n[LINKS] Total: {len(links)}")
    for link in links:
        if link['href'] and not link['href'].startswith('https://www.pokergo.com/_nuxt'):
            print(f"  {link['text'][:40]:40} -> {link['href']}")

    # 페이지 텍스트
    print("\n[PAGE TEXT]")
    text = await page.evaluate('() => document.body.innerText')
    print(text[:3000])

    # 클릭 가능한 카드 요소 찾기
    print("\n\n[INFO] Looking for clickable cards...")

    # swiper 슬라이드 내부의 요소 찾기
    cards = await page.locator('.swiper-slide a, [class*="SeriesCard"] a, [class*="series"] a').all()
    print(f"  Found {len(cards)} cards via locator")

    for i, card in enumerate(cards[:10]):
        try:
            href = await card.get_attribute('href')
            text = await card.inner_text()
            print(f"    Card {i}: {text[:50]} -> {href}")
        except Exception:
            pass

    # 이미지 기반으로 시리즈 찾기
    print("\n[INFO] Looking for series by images...")
    images = await page.locator('img[src*="wsop"], img[alt*="WSOP"]').all()
    print(f"  Found {len(images)} WSOP images")

    for i, img in enumerate(images[:10]):
        try:
            _src = await img.get_attribute('src')  # stored for potential debugging
            alt = await img.get_attribute('alt')
            # 부모 링크 찾기
            parent_link = await img.locator('xpath=ancestor::a').first
            href = await parent_link.get_attribute('href') if parent_link else None
            print(f"    Img {i}: {alt[:30] if alt else 'no alt'} -> {href}")
        except Exception as e:
            print(f"    Img {i}: Error - {e}")

    await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
