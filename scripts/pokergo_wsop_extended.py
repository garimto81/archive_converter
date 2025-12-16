"""
PokerGO WSOP Extended Scraper

추가 수집:
- WSOP Classic (2003-2010)
- WSOP Europe
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
    print("PokerGO WSOP Extended Scraper")
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

        email_input = page.locator('input[placeholder="Email Address"]')
        pwd_input = page.locator('input[placeholder="Password"]')
        login_btn = page.locator('button:has-text("Login")')

        await email_input.fill(POKERGO_ID)
        await asyncio.sleep(0.5)
        await pwd_input.fill(POKERGO_PASSWORD)
        await asyncio.sleep(0.5)

        print(f"  Email: {POKERGO_ID}")
        print(f"  Password: {'*' * len(POKERGO_PASSWORD)}")

        await login_btn.click()
        print("  Clicked login button...")

        await asyncio.sleep(5)

        if "login" in page.url.lower():
            print("  [WARN] Still on login page - trying Enter key")
            await pwd_input.press("Enter")
            await asyncio.sleep(5)

        if "login" not in page.url.lower():
            print("  [OK] Login successful!")
        else:
            print("  [ERROR] Login failed")
            print("  Continuing anyway...")

        # === COLLECT VIDEOS ===
        print("\n[2/3] COLLECTING WSOP VIDEOS (Extended)")

        collections = [
            # WSOP Classic (2003-2010)
            ("2010 Classic", "https://www.pokergo.com/collections/wsop-2010"),
            ("2009 Classic", "https://www.pokergo.com/collections/wsop-2009"),
            ("2008 Classic", "https://www.pokergo.com/collections/wsop-2008"),
            ("2007 Classic", "https://www.pokergo.com/collections/wsop-2007"),
            ("2006 Classic", "https://www.pokergo.com/collections/wsop-2006"),
            ("2005 Classic", "https://www.pokergo.com/collections/wsop-2005"),
            ("2004 Classic", "https://www.pokergo.com/collections/wsop-2004"),
            ("2003 Classic", "https://www.pokergo.com/collections/wsop-2003"),

            # Alternative Classic URL patterns
            ("2010 Main Event", "https://www.pokergo.com/collections/wsop-2010-main-event"),
            ("2009 Main Event", "https://www.pokergo.com/collections/wsop-2009-main-event"),
            ("2008 Main Event", "https://www.pokergo.com/collections/wsop-2008-main-event"),
            ("2007 Main Event", "https://www.pokergo.com/collections/wsop-2007-main-event"),
            ("2006 Main Event", "https://www.pokergo.com/collections/wsop-2006-main-event"),
            ("2005 Main Event", "https://www.pokergo.com/collections/wsop-2005-main-event"),
            ("2004 Main Event", "https://www.pokergo.com/collections/wsop-2004-main-event"),
            ("2003 Main Event", "https://www.pokergo.com/collections/wsop-2003-main-event"),

            # WSOP Classic collection page
            ("WSOP Classic", "https://www.pokergo.com/collections/wsop-classic"),
            ("WSOP Classic ME", "https://www.pokergo.com/collections/wsop-classic-main-event"),

            # WSOP Europe (confirmed URL)
            ("WSOP Europe", "https://www.pokergo.com/collections/world-series-of-poker-europe"),
            ("WSOPE 2023", "https://www.pokergo.com/collections/wsop-europe-2023"),
            ("WSOPE 2022", "https://www.pokergo.com/collections/wsop-europe-2022"),
            ("WSOPE 2021", "https://www.pokergo.com/collections/wsop-europe-2021"),
            ("WSOPE 2019", "https://www.pokergo.com/collections/wsop-europe-2019"),
            ("WSOPE 2018", "https://www.pokergo.com/collections/wsop-europe-2018"),
            ("WSOPE 2017", "https://www.pokergo.com/collections/wsop-europe-2017"),
            ("WSOPE ME", "https://www.pokergo.com/collections/wsop-europe-main-event"),
            ("WSOPE Bracelet", "https://www.pokergo.com/collections/wsop-europe-bracelet-events"),
            ("WSOPE All", "https://www.pokergo.com/collections/world-series-of-poker-europe"),

            # Try searching for wsop-classic
            ("WSOP Archives", "https://www.pokergo.com/collections/wsop-archives"),
            ("WSOP History", "https://www.pokergo.com/collections/wsop-history"),
        ]

        for name, url in collections:
            print(f"\n  [{name}]")
            prev_count = len(all_videos)

            try:
                await page.goto(url, timeout=30000)
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)

                # Check if page exists (not 404)
                page_title = await page.title()
                if "404" in page_title or "not found" in page_title.lower():
                    print("    [SKIP] Page not found")
                    continue

                # Scroll to load all content
                for _ in range(10):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)

                # Find all video links
                video_links = page.locator('a[href*="/videos/"]')
                count = await video_links.count()

                for i in range(count):
                    try:
                        link = video_links.nth(i)
                        href = await link.get_attribute("href")
                        if not href:
                            continue

                        full_url = href if href.startswith("http") else f"https://www.pokergo.com{href}"

                        # Skip duplicates
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
                if added > 0:
                    print(f"    +{added} videos (total: {len(all_videos)})")
                else:
                    print("    No new videos found")

            except Exception as e:
                print(f"    [ERROR] {str(e)[:60]}")

        # === Also try search ===
        print("\n  [Search: WSOP Classic]")
        try:
            await page.goto("https://www.pokergo.com/search?q=wsop%20classic", timeout=30000)
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # Scroll
            for _ in range(5):
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)

            video_links = page.locator('a[href*="/videos/"]')
            count = await video_links.count()
            prev_count = len(all_videos)

            for i in range(count):
                try:
                    link = video_links.nth(i)
                    href = await link.get_attribute("href")
                    if not href:
                        continue
                    full_url = href if href.startswith("http") else f"https://www.pokergo.com{href}"
                    if any(v.get("url") == full_url for v in all_videos):
                        continue
                    title_el = link.locator("h2, h3, h4, [class*='title']").first
                    title = ""
                    try:
                        title = await title_el.text_content(timeout=1000)
                    except Exception:
                        pass
                    all_videos.append({
                        "url": full_url,
                        "slug": href.split("/")[-1].split("?")[0],
                        "title": (title or "").strip(),
                        "thumbnail": "",
                        "source": "Search: WSOP Classic",
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
            url = v.get("url", "")
            for year in range(2003, 2026):
                if str(year) in source or str(year) in title or str(year) in url:
                    v["year"] = year
                    break

        # Determine category
        for v in all_videos:
            source = v.get("source", "").lower()
            title = v.get("title", "").lower()
            if "europe" in source or "europe" in title or "wsope" in source:
                v["category"] = "WSOP Europe"
            elif "classic" in source or int(v.get("year", 2020)) <= 2010:
                v["category"] = "WSOP Classic"
            else:
                v["category"] = "WSOP"

        # Count by year
        year_counts = {}
        for v in all_videos:
            y = v.get("year", "unknown")
            year_counts[y] = year_counts.get(y, 0) + 1

        # Count by category
        cat_counts = {}
        for v in all_videos:
            c = v.get("category", "unknown")
            cat_counts[c] = cat_counts.get(c, 0) + 1

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
            "by_category": cat_counts,
            "videos": all_videos,
        }

        output_file = OUTPUT_DIR / f"wsop_extended_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[RESULT]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print(f"  Total: {len(all_videos)} videos")
        print("\n[BY CATEGORY]")
        for c, count in sorted(cat_counts.items()):
            print(f"  {c}: {count}")
        print("\n[BY YEAR]")
        for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
            print(f"  {y}: {c}")

    finally:
        await browser.close()
        print("\n[INFO] Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
