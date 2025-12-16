"""
PokerGO Deep Scraper

하위 계층까지 재귀적으로 탐색:
- WSOP Classic -> 2004 -> Main Event -> 개별 비디오
- WSOP Classic -> 2004 -> Bracelet Events -> 개별 비디오
- WSOP Europe -> 년도별 -> Main Event / Bracelet Events
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

# 이미 방문한 URL
visited_urls = set()
all_videos = []


async def collect_videos_from_page(page, source_name: str) -> int:
    """현재 페이지에서 비디오 링크 수집"""
    global all_videos

    added = 0
    video_links = page.locator('a[href*="/videos/"]')
    count = await video_links.count()

    for i in range(count):
        try:
            link = video_links.nth(i)
            href = await link.get_attribute("href")
            if not href:
                continue

            full_url = href if href.startswith("http") else f"https://www.pokergo.com{href}"

            # 중복 체크
            if any(v.get("url") == full_url for v in all_videos):
                continue

            # 제목
            title = ""
            try:
                title_el = link.locator("h2, h3, h4, [class*='title'], [class*='Title']").first
                title = await title_el.text_content(timeout=1000)
            except:
                pass

            # 썸네일
            thumbnail = ""
            try:
                img = link.locator("img").first
                thumbnail = await img.get_attribute("src", timeout=1000)
            except:
                pass

            all_videos.append({
                "url": full_url,
                "slug": href.split("/")[-1].split("?")[0],
                "title": (title or "").strip(),
                "thumbnail": thumbnail or "",
                "source": source_name,
            })
            added += 1

        except Exception as e:
            continue

    return added


async def find_sub_collections(page) -> list:
    """현재 페이지에서 하위 컬렉션 링크 찾기"""
    sub_collections = []

    # 컬렉션 링크 패턴
    collection_links = page.locator('a[href*="/collections/"]')
    count = await collection_links.count()

    for i in range(count):
        try:
            link = collection_links.nth(i)
            href = await link.get_attribute("href")
            if not href:
                continue

            full_url = href if href.startswith("http") else f"https://www.pokergo.com{href}"

            # 이미 방문했으면 스킵
            if full_url in visited_urls:
                continue

            # 이름 추출
            name = ""
            try:
                name = await link.text_content(timeout=1000)
                name = (name or "").strip()
            except:
                name = href.split("/")[-1]

            sub_collections.append({
                "url": full_url,
                "name": name,
            })

        except:
            continue

    return sub_collections


async def scrape_collection(page, url: str, name: str, depth: int = 0):
    """컬렉션 페이지 스크래핑 (재귀)"""
    global visited_urls

    if url in visited_urls:
        return
    visited_urls.add(url)

    indent = "  " * depth
    print(f"{indent}[{name}] {url}")

    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)

        # 스크롤
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(0.5)

        # 비디오 수집
        added = await collect_videos_from_page(page, name)
        if added > 0:
            print(f"{indent}  +{added} videos (total: {len(all_videos)})")

        # 하위 컬렉션 찾기
        sub_collections = await find_sub_collections(page)

        if sub_collections:
            print(f"{indent}  Found {len(sub_collections)} sub-collections")
            for sub in sub_collections:
                await scrape_collection(page, sub["url"], f"{name} > {sub['name']}", depth + 1)

    except Exception as e:
        print(f"{indent}  [ERROR] {str(e)[:50]}")


async def main():
    global all_videos, visited_urls

    print("=" * 60)
    print("PokerGO Deep Scraper")
    print("=" * 60)

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
        await login_btn.click()
        await asyncio.sleep(5)

        if "login" not in page.url.lower():
            print("  [OK] Login successful!")
        else:
            print("  [WARN] May not be logged in")

        # === DEEP SCRAPE ===
        print("\n[2/3] DEEP SCRAPING")

        # 루트 컬렉션들
        root_collections = [
            ("WSOP Classic", "https://www.pokergo.com/collections/wsop-classic"),
            ("WSOP Europe", "https://www.pokergo.com/collections/world-series-of-poker-europe"),
        ]

        for name, url in root_collections:
            print(f"\n{'='*40}")
            print(f"ROOT: {name}")
            print(f"{'='*40}")
            await scrape_collection(page, url, name, depth=0)

        # === SAVE ===
        print("\n[3/3] SAVING DATA")

        # 연도 추출
        import re
        for v in all_videos:
            slug = v.get("slug", "")
            source = v.get("source", "")
            title = v.get("title", "")

            year = None
            for text in [slug, source, title]:
                match = re.search(r'(19\d{2}|20\d{2})', text)
                if match:
                    year = int(match.group(1))
                    break
            v["year"] = year

            # 카테고리
            source_lower = source.lower()
            if "europe" in source_lower:
                v["category"] = "WSOP Europe"
            elif "classic" in source_lower or (year and year <= 2010):
                v["category"] = "WSOP Classic"
            else:
                v["category"] = "WSOP"

            # 제목 생성 (없으면)
            if not v.get("title"):
                v["title"] = slug.replace("-", " ").title()

        # 통계
        year_counts = {}
        cat_counts = {}
        for v in all_videos:
            y = v.get("year", "unknown")
            c = v.get("category", "unknown")
            year_counts[y] = year_counts.get(y, 0) + 1
            cat_counts[c] = cat_counts.get(c, 0) + 1

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output = {
            "scraped_at": datetime.now().isoformat(),
            "total_videos": len(all_videos),
            "by_year": dict(sorted([(str(k), v) for k, v in year_counts.items()], reverse=True)),
            "by_category": cat_counts,
            "videos": all_videos,
        }

        output_file = OUTPUT_DIR / f"wsop_deep_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print("[RESULT]")
        print(f"{'='*60}")
        print(f"  File: {output_file}")
        print(f"  Total: {len(all_videos)} videos")
        print(f"\n[BY CATEGORY]")
        for c, count in sorted(cat_counts.items()):
            print(f"  {c}: {count}")
        print(f"\n[BY YEAR]")
        for y, c in sorted(year_counts.items(), key=lambda x: str(x[0]), reverse=True):
            print(f"  {y}: {c}")

    finally:
        await browser.close()
        print("\n[INFO] Browser closed")


if __name__ == "__main__":
    asyncio.run(main())
