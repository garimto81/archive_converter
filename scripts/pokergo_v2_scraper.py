"""
PokerGO WSOP Scraper v2

Playwright locator API 사용 - 더 안정적인 요소 선택
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


async def main():
    print("=" * 60)
    print("PokerGO WSOP Scraper v2")
    print("=" * 60)
    print(f"Account: {POKERGO_ID}")

    all_videos = []

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    try:
        # === LOGIN ===
        print("\n[1/3] LOGIN")
        await page.goto("https://www.pokergo.com/login")
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # Use locator API - more reliable than query_selector
        email_input = page.locator('input[placeholder="Email Address"]')
        pwd_input = page.locator('input[placeholder="Password"]')
        login_btn = page.locator('button:has-text("Login")')

        # Fill credentials
        await email_input.fill(POKERGO_ID)
        await asyncio.sleep(0.5)
        await pwd_input.fill(POKERGO_PASSWORD)
        await asyncio.sleep(0.5)

        print(f"  Email: {POKERGO_ID}")
        print(f"  Password: {'*' * len(POKERGO_PASSWORD)}")

        # Click login
        await login_btn.click()
        print("  Clicked login button...")

        # Wait for navigation
        await asyncio.sleep(5)

        if "login" in page.url.lower():
            print("  [WARN] Still on login page - trying Enter key")
            await pwd_input.press("Enter")
            await asyncio.sleep(5)

        if "login" not in page.url.lower():
            print("  [OK] Login successful!")
        else:
            print("  [ERROR] Login failed - check credentials")
            # Continue anyway to see what's available without login
            print("  Continuing without login...")

        # === COLLECT VIDEOS ===
        print("\n[2/3] COLLECTING WSOP VIDEOS")

        # Collection URLs that worked before
        collections = [
            # 2025
            ("2025 Main Event", "https://www.pokergo.com/collections/wsop-2025-main-event"),
            ("2025 Bracelet", "https://www.pokergo.com/collections/wsop-2025-bracelet-events"),
            # 2024
            ("2024 ME Episodes", "https://www.pokergo.com/collections/wsop-2024-main-event--episodes"),
            ("2024 ME Live", "https://www.pokergo.com/collections/wsop-2024-main-event"),
            ("2024 BE Episodes", "https://www.pokergo.com/collections/wsop-2024-bracelet-events--episodes"),
            ("2024 BE Live", "https://www.pokergo.com/collections/wsop-2024-bracelet-events"),
            # 2023
            ("2023 Main Event", "https://www.pokergo.com/collections/wsop-2023-main-event"),
            ("2023 Bracelet", "https://www.pokergo.com/collections/wsop-2023-bracelet-events"),
            # 2022
            ("2022 Main Event", "https://www.pokergo.com/collections/wsop-2022-main-event"),
            ("2022 Bracelet", "https://www.pokergo.com/collections/wsop-2022-bracelet-events"),
            # 2021
            ("2021 Main Event", "https://www.pokergo.com/collections/wsop-2021-main-event"),
            ("2021 Bracelet", "https://www.pokergo.com/collections/wsop-2021-bracelet-events"),
            # 2019-2011
            ("2019 Main Event", "https://www.pokergo.com/collections/wsop-2019-main-event"),
            ("2019 Bracelet", "https://www.pokergo.com/collections/wsop-2019-bracelet-events"),
            ("2018 Main Event", "https://www.pokergo.com/collections/wsop-2018-main-event"),
            ("2017 Main Event", "https://www.pokergo.com/collections/wsop-2017-main-event"),
            ("2016 Main Event", "https://www.pokergo.com/collections/wsop-2016-main-event"),
            ("2015 Main Event", "https://www.pokergo.com/collections/wsop-2015-main-event"),
            ("2014 Main Event", "https://www.pokergo.com/collections/wsop-2014-main-event"),
            ("2013 Main Event", "https://www.pokergo.com/collections/wsop-2013-main-event"),
            ("2012 Main Event", "https://www.pokergo.com/collections/wsop-2012-main-event"),
            ("2011 Main Event", "https://www.pokergo.com/collections/wsop-2011-main-event"),
        ]

        for name, url in collections:
            print(f"\n  [{name}]")
            prev_count = len(all_videos)

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # Scroll to load all content
                for _ in range(10):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)

                # Find all video links using locator
                video_links = page.locator('a[href*="/videos/"]')
                count = await video_links.count()

                for i in range(count):
                    try:
                        link = video_links.nth(i)
                        href = await link.get_attribute("href")
                        if not href:
                            continue

                        full_url = href if href.startswith("http") else f"https://www.pokergo.com{href}"

                        # Skip if already collected
                        if any(v.get("url") == full_url for v in all_videos):
                            continue

                        # Get title
                        title_el = link.locator("h2, h3, h4, [class*='title']").first
                        title = ""
                        try:
                            title = await title_el.text_content(timeout=1000)
                        except Exception:
                            pass

                        # Get thumbnail
                        img = link.locator("img").first
                        thumbnail = ""
                        try:
                            thumbnail = await img.get_attribute("src", timeout=1000)
                        except Exception:
                            pass

                        all_videos.append({
                            "url": full_url,
                            "slug": href.split("/")[-1].split("?")[0],
                            "title": (title or "").strip(),
                            "thumbnail": thumbnail or "",
                            "source": name,
                        })

                    except Exception:
                        continue

                added = len(all_videos) - prev_count
                print(f"    +{added} videos (total: {len(all_videos)})")

            except Exception as e:
                print(f"    [ERROR] {str(e)[:60]}")

        # === SAVE DATA ===
        print("\n[3/3] SAVING DATA")

        # Extract year from title/source
        for v in all_videos:
            source = v.get("source", "")
            title = v.get("title", "")
            for year in range(2011, 2026):
                if str(year) in source or str(year) in title:
                    v["year"] = year
                    break

        # Count by year
        year_counts = {}
        for v in all_videos:
            y = v.get("year", "unknown")
            year_counts[y] = year_counts.get(y, 0) + 1

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
            "videos": all_videos,
        }

        output_file = OUTPUT_DIR / f"wsop_v2_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[RESULT]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print(f"  Total: {len(all_videos)} videos")
        print("\n[BY YEAR]")
        for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
            print(f"  {y}: {c}")

    finally:
        await browser.close()
        print("\n[INFO] Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
