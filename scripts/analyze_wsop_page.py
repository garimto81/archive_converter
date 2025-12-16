"""
PokerGO WSOP 페이지 구조 분석
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
    print("Analyzing PokerGO WSOP Page Structure")
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

    print("[INFO] Going to WSOP page...")
    await page.goto("https://www.pokergo.com/wsop", wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # Screenshot
    await page.screenshot(path=str(DATA_DIR / "wsop_page.png"), full_page=True)
    print(f"[INFO] Screenshot saved to: {DATA_DIR / 'wsop_page.png'}")

    # Analyze page structure
    print("\n[INFO] Analyzing page structure...")

    # Get all links
    all_links = await page.evaluate('''() => {
        const links = [];
        document.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href') || '';
            links.push({
                href: href,
                text: a.textContent?.trim()?.substring(0, 100) || '',
                classes: a.className || ''
            });
        });
        return links;
    }''')

    print(f"\n[LINKS] Total links: {len(all_links)}")

    # Filter interesting links
    video_links = [link for link in all_links if '/videos/' in link.get('href', '') or '/watch/' in link.get('href', '')]
    season_links = [link for link in all_links if '/season' in link.get('href', '').lower()]
    wsop_links = [link for link in all_links if 'wsop' in link.get('href', '').lower()]

    print(f"\n[VIDEO LINKS] {len(video_links)}")
    for link in video_links[:10]:
        print(f"  - {link['href'][:80]}")

    print(f"\n[SEASON LINKS] {len(season_links)}")
    for link in season_links[:10]:
        print(f"  - {link['href']}")

    print(f"\n[WSOP LINKS] {len(wsop_links)}")
    for link in wsop_links[:20]:
        print(f"  - {link['href']}")

    # Look for any navigation elements
    nav_items = await page.evaluate('''() => {
        const items = [];
        // Look for season/year selectors
        document.querySelectorAll('[class*="season"], [class*="year"], select, [role="listbox"]').forEach(el => {
            items.push({
                tag: el.tagName,
                class: el.className || '',
                id: el.id || '',
                text: el.textContent?.trim()?.substring(0, 200) || ''
            });
        });
        return items;
    }''')

    print(f"\n[NAV ITEMS] {len(nav_items)}")
    for item in nav_items[:10]:
        print(f"  - {item['tag']}: {item['class'][:50]} | {item['text'][:50]}")

    # Check for any API calls in network
    print("\n[INFO] Page URL:", page.url)

    await browser.close()
    print("\n[DONE]")


if __name__ == "__main__":
    asyncio.run(main())
