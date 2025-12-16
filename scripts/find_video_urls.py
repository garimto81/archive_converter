# -*- coding: utf-8 -*-
"""
PokerGO 유효한 비디오 URL 찾기
"""
import asyncio
import os
import sys
import json
from dotenv import load_dotenv
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(Path(__file__).parent.parent / ".env")
POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo" / "downloads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class VideoFinder:
    def __init__(self):
        self.api_responses = []

    async def capture_response(self, response):
        url = response.url
        if "api.pokergo.com" in url and response.status == 200:
            try:
                content_type = response.headers.get("content-type", "")
                if "json" in content_type:
                    data = await response.json()
                    self.api_responses.append({"url": url, "data": data})
            except Exception:
                pass


async def main():
    finder = VideoFinder()

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1920, "height": 1080})
    page = await context.new_page()

    page.on("response", finder.capture_response)

    # 로그인
    print("[INFO] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)

    await page.fill('input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("Login")')
    await page.wait_for_timeout(5000)

    # On Demand 페이지 방문
    print("[INFO] Opening On Demand page...")
    await page.goto("https://www.pokergo.com/on-demand", wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # 스크롤
    for _ in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1000)

    # 페이지에서 비디오 링크 추출
    video_links = await page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a[href*="/videos/"]').forEach(a => {
            const href = a.href;
            const text = a.innerText || a.textContent || '';
            if (href && !links.some(l => l.href === href)) {
                links.push({href: href, text: text.substring(0, 50)});
            }
        });
        return links.slice(0, 20);
    }""")

    print(f"[INFO] Found {len(video_links)} video links on page")
    for link in video_links[:10]:
        print(f"  {link['href']} - {link['text']}")

    # API 응답에서 비디오 찾기
    print(f"\n[INFO] Captured {len(finder.api_responses)} API responses")

    videos_from_api = []
    for resp in finder.api_responses:
        data = resp["data"]
        if isinstance(data, dict) and "data" in data:
            inner = data["data"]
            if isinstance(inner, dict):
                for key in ["view_videos", "videos", "recently_added", "view_collections"]:
                    items = inner.get(key, [])
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                # view_collections의 경우 videos 안에 있음
                                if "videos" in item:
                                    for v in item["videos"]:
                                        if isinstance(v, dict):
                                            vid = v.get("id", "")
                                            slug = v.get("slug", "")
                                            title = v.get("title", "")
                                            if vid:
                                                videos_from_api.append({
                                                    "id": vid,
                                                    "slug": slug,
                                                    "title": title[:50]
                                                })
                                else:
                                    vid = item.get("id", "")
                                    slug = item.get("slug", "")
                                    title = item.get("title", "")
                                    if vid:
                                        videos_from_api.append({
                                            "id": vid,
                                            "slug": slug,
                                            "title": title[:50]
                                        })

    # 중복 제거
    seen = set()
    unique_videos = []
    for v in videos_from_api:
        if v["id"] not in seen:
            seen.add(v["id"])
            unique_videos.append(v)

    print(f"[INFO] Found {len(unique_videos)} unique videos from API")
    for v in unique_videos[:15]:
        print(f"  ID: {v['id']} | slug: {v['slug']} | {v['title']}")

    # 저장
    result = {
        "video_links": video_links,
        "videos_from_api": unique_videos
    }
    with open(OUTPUT_DIR / "video_discovery.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Saved to {OUTPUT_DIR / 'video_discovery.json'}")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
