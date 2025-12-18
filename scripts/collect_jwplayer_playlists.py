# -*- coding: utf-8 -*-
"""
PokerGO JWPlayer Playlist 전체 수집

모든 비디오 페이지를 순회하여 JWPlayer playlist 정보 수집
- HLS URL, MP4 URL (각 해상도별)
- 비디오 메타데이터 (제목, 길이, mediaid 등)
"""
import asyncio
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(Path(__file__).parent.parent / ".env")
POKERGO_ID = os.getenv("POKERGO_ID")
POKERGO_PASSWORD = os.getenv("POKERGO_PASSWORD")

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "pokergo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class PlaylistCollector:
    def __init__(self):
        self.browser = None
        self.page = None
        self.video_ids = set()
        self.playlists = []
        self.errors = []

    async def start(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await context.new_page()
        print("[INFO] Browser started")

    async def login(self):
        print("[INFO] Logging in...")
        await self.page.goto("https://www.pokergo.com/login", wait_until="networkidle")
        await self.page.wait_for_timeout(2000)

        await self.page.fill('input[name="email"]', POKERGO_ID)
        await self.page.fill('input[type="password"]', POKERGO_PASSWORD)
        await self.page.click('button:has-text("Login")')
        await self.page.wait_for_timeout(5000)

        if "login" not in self.page.url.lower():
            print("[OK] Login successful!")
            return True
        print("[ERROR] Login failed")
        return False

    async def collect_video_ids(self):
        """여러 페이지에서 비디오 ID 수집"""
        print("\n[INFO] Collecting video IDs from pages...")

        pages_to_visit = [
            ("Home", "https://www.pokergo.com/"),
            ("On Demand", "https://www.pokergo.com/on-demand"),
            ("Shows", "https://www.pokergo.com/shows"),
            ("WSOP", "https://www.pokergo.com/wsop"),
        ]

        for name, url in pages_to_visit:
            print(f"  [PAGE] {name}: {url}")
            try:
                await self.page.goto(url, wait_until="networkidle")
                await self.page.wait_for_timeout(2000)

                # 스크롤하여 더 많은 콘텐츠 로드
                for _ in range(5):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1000)

                # 비디오 링크 추출
                links = await self.page.evaluate("""() => {
                    const links = [];
                    document.querySelectorAll('a[href*="/videos/"]').forEach(a => {
                        const href = a.href;
                        const match = href.match(/\\/videos\\/([a-zA-Z0-9-]+)/);
                        if (match && match[1]) {
                            links.push(match[1]);
                        }
                    });
                    return [...new Set(links)];
                }""")

                for vid in links:
                    self.video_ids.add(vid)

                print(f"    Found {len(links)} videos (Total: {len(self.video_ids)})")

            except Exception as e:
                print(f"    [ERROR] {e}")

        # 추가 검색 쿼리
        search_queries = ["WSOP", "High Stakes Poker", "Poker After Dark", "WPT"]
        for query in search_queries:
            print(f"  [SEARCH] {query}")
            try:
                await self.page.goto(
                    f"https://www.pokergo.com/search?q={query}",
                    wait_until="networkidle"
                )
                await self.page.wait_for_timeout(2000)

                for _ in range(3):
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await self.page.wait_for_timeout(1000)

                links = await self.page.evaluate("""() => {
                    const links = [];
                    document.querySelectorAll('a[href*="/videos/"]').forEach(a => {
                        const href = a.href;
                        const match = href.match(/\\/videos\\/([a-zA-Z0-9-]+)/);
                        if (match && match[1]) {
                            links.push(match[1]);
                        }
                    });
                    return [...new Set(links)];
                }""")

                for vid in links:
                    self.video_ids.add(vid)

                print(f"    Found {len(links)} videos (Total: {len(self.video_ids)})")

            except Exception as e:
                print(f"    [ERROR] {e}")

        print(f"\n[RESULT] Total unique video IDs: {len(self.video_ids)}")

    async def extract_playlist(self, video_id: str) -> dict:
        """단일 비디오 페이지에서 JWPlayer playlist 추출"""
        url = f"https://www.pokergo.com/videos/{video_id}"

        try:
            await self.page.goto(url, wait_until="networkidle")
            await self.page.wait_for_timeout(2000)

            # JWPlayer playlist 추출
            playlist_data = await self.page.evaluate("""() => {
                if (typeof jwplayer === 'undefined') return null;

                try {
                    const player = jwplayer();
                    if (!player) return null;

                    const playlist = player.getPlaylist();
                    if (!playlist || !playlist.length) return null;

                    const item = playlist[0];

                    // 소스 URL 정리
                    const sources = [];
                    const allSources = item.allSources || item.sources || [];

                    for (const src of allSources) {
                        sources.push({
                            type: src.type,
                            file: src.file,
                            label: src.label,
                            height: src.height,
                            width: src.width,
                            bitrate: src.bitrate,
                            filesize: src.filesize
                        });
                    }

                    return {
                        title: item.title,
                        mediaid: item.mediaid,
                        duration: item.duration,
                        image: item.image,
                        description: item.description,
                        pubdate: item.pubdate,
                        sources: sources,
                        tracks: item.tracks,
                        // PokerGO 메타데이터
                        vch_id: item['VCH.ID'],
                        vch_drm: item['VCH.DRM'],
                        vch_event_state: item['VCH.EventState']
                    };
                } catch(e) {
                    return {error: e.message};
                }
            }""")

            if playlist_data and not playlist_data.get('error'):
                playlist_data['video_id'] = video_id
                playlist_data['page_url'] = url
                return playlist_data
            else:
                return None

        except Exception as e:
            self.errors.append({'video_id': video_id, 'error': str(e)})
            return None

    async def collect_all_playlists(self, limit: int = None):
        """모든 비디오의 playlist 수집"""
        video_ids = list(self.video_ids)
        if limit:
            video_ids = video_ids[:limit]

        total = len(video_ids)
        print(f"\n[INFO] Collecting playlists from {total} videos...")

        for i, vid in enumerate(video_ids):
            print(f"  [{i+1}/{total}] {vid}...", end=" ")

            playlist = await self.extract_playlist(vid)

            if playlist:
                self.playlists.append(playlist)
                title = playlist.get('title', 'Unknown')[:40]
                sources_count = len(playlist.get('sources', []))
                print(f"OK - {title} ({sources_count} sources)")
            else:
                print("SKIP (no playlist)")

            # Rate limiting
            await self.page.wait_for_timeout(500)

    async def close(self):
        if self.browser:
            await self.browser.close()
            print("[INFO] Browser closed")

    def save_results(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 전체 결과 저장
        result = {
            "collected_at": datetime.now().isoformat(),
            "total_video_ids": len(self.video_ids),
            "total_playlists": len(self.playlists),
            "total_errors": len(self.errors),
            "video_ids": list(self.video_ids),
            "playlists": self.playlists,
            "errors": self.errors
        }

        output_file = OUTPUT_DIR / f"jwplayer_playlists_{timestamp}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVED] {output_file}")

        # 다운로드 URL만 따로 저장 (간단한 형식)
        download_urls = []
        for p in self.playlists:
            video_info = {
                "video_id": p.get("video_id"),
                "title": p.get("title"),
                "duration": p.get("duration"),
                "mediaid": p.get("mediaid"),
                "urls": {}
            }

            for src in p.get("sources", []):
                src_type = src.get("type", "unknown")
                label = src.get("label", src_type)
                file_url = src.get("file", "")

                if src_type == "hls":
                    video_info["urls"]["hls"] = file_url
                elif src_type == "mp4":
                    video_info["urls"][f"mp4_{label}"] = file_url

            download_urls.append(video_info)

        urls_file = OUTPUT_DIR / f"download_urls_{timestamp}.json"
        with open(urls_file, "w", encoding="utf-8") as f:
            json.dump(download_urls, f, ensure_ascii=False, indent=2)

        print(f"[SAVED] {urls_file}")

        # 통계 출력
        print(f"\n{'='*60}")
        print("[STATISTICS]")
        print(f"{'='*60}")
        print(f"  Video IDs found: {len(self.video_ids)}")
        print(f"  Playlists collected: {len(self.playlists)}")
        print(f"  Errors: {len(self.errors)}")

        # 소스 타입별 통계
        source_types = {}
        total_size = 0
        for p in self.playlists:
            for src in p.get("sources", []):
                label = src.get("label", src.get("type", "unknown"))
                if label not in source_types:
                    source_types[label] = 0
                source_types[label] += 1
                total_size += src.get("filesize") or 0

        print("\n  Source types:")
        for label, count in sorted(source_types.items()):
            print(f"    {label}: {count}")

        print(f"\n  Total file size (all qualities): {total_size / 1024 / 1024 / 1024:.2f} GB")


async def main():
    print("=" * 60)
    print("PokerGO JWPlayer Playlist Collector")
    print("=" * 60)

    collector = PlaylistCollector()

    try:
        await collector.start()

        if await collector.login():
            await collector.collect_video_ids()
            await collector.collect_all_playlists()  # limit=10 for testing
            collector.save_results()

    finally:
        await collector.close()


if __name__ == "__main__":
    asyncio.run(main())
