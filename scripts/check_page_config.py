# -*- coding: utf-8 -*-
"""
PokerGO 페이지 전역 설정 확인
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


async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()

    # 로그인
    print("[1] Logging in...")
    await page.goto("https://www.pokergo.com/login", wait_until="networkidle")
    await page.wait_for_timeout(2000)
    await page.fill('input[name="email"]', POKERGO_ID)
    await page.fill('input[type="password"]', POKERGO_PASSWORD)
    await page.click('button:has-text("Login")')
    await page.wait_for_timeout(5000)

    # 비디오 페이지
    print("[2] Opening video page...")
    await page.goto(
        "https://www.pokergo.com/videos/422cf804-6fd8-4e41-a5fb-29fe1e5a4ef7",
        wait_until="networkidle"
    )
    await page.wait_for_timeout(3000)

    # 전역 설정 확인
    print("[3] Checking global page settings...\n")

    # JWPlayer 확인
    jw_info = await page.evaluate("""() => {
        if (typeof jwplayer === 'undefined') return null;

        try {
            const player = jwplayer();
            if (!player) return null;

            return {
                state: player.getState ? player.getState() : null,
                playlist: player.getPlaylist ? player.getPlaylist() : null,
                position: player.getPosition ? player.getPosition() : null,
                duration: player.getDuration ? player.getDuration() : null,
                volume: player.getVolume ? player.getVolume() : null,
                mute: player.getMute ? player.getMute() : null,
                fullscreen: player.getFullscreen ? player.getFullscreen() : null
            };
        } catch(e) {
            return {error: e.message};
        }
    }""")

    print("=== JWPlayer Info ===")
    print(json.dumps(jw_info, indent=2, ensure_ascii=False))

    # Window 전역 변수 검색
    window_keys = await page.evaluate("""() => {
        const found = [];
        const keywords = ['video', 'player', 'stream', 'hls', 'config', 'poker', 'media', 'source'];

        for (let key in window) {
            const lk = key.toLowerCase();
            for (let kw of keywords) {
                if (lk.includes(kw)) {
                    try {
                        const val = window[key];
                        if (val !== null && val !== undefined && typeof val !== 'function') {
                            found.push({
                                key: key,
                                type: typeof val,
                                preview: JSON.stringify(val).substring(0, 300)
                            });
                        }
                    } catch(e) {}
                    break;
                }
            }
        }
        return found;
    }""")

    print("\n=== Window Global Variables (video/player related) ===")
    for item in window_keys[:20]:
        print(f"  {item['key']} ({item['type']}): {item['preview'][:100]}...")

    # __NEXT_DATA__ 확인 (Next.js)
    next_data = await page.evaluate("""() => {
        const script = document.getElementById('__NEXT_DATA__');
        if (script) {
            try {
                return JSON.parse(script.textContent);
            } catch(e) {
                return null;
            }
        }
        return null;
    }""")

    print("\n=== __NEXT_DATA__ (Next.js) ===")
    if next_data:
        print(f"  buildId: {next_data.get('buildId', 'N/A')}")
        print(f"  page: {next_data.get('page', 'N/A')}")
        if 'props' in next_data and 'pageProps' in next_data['props']:
            page_props = next_data['props']['pageProps']
            print(f"  pageProps keys: {list(page_props.keys())[:10]}")

            # 비디오 관련 데이터 찾기
            if 'video' in page_props:
                print("\n  Video Data Found!")
                video_data = page_props['video']
                print(json.dumps(video_data, indent=2, ensure_ascii=False)[:1000])
    else:
        print("  Not found (not a Next.js app)")

    # Redux/Preloaded State 확인
    preloaded = await page.evaluate("""() => {
        if (window.__PRELOADED_STATE__) return window.__PRELOADED_STATE__;
        if (window.__REDUX_STATE__) return window.__REDUX_STATE__;
        if (window.__INITIAL_STATE__) return window.__INITIAL_STATE__;
        return null;
    }""")

    print("\n=== Preloaded/Redux State ===")
    if preloaded:
        print(json.dumps(preloaded, indent=2, ensure_ascii=False)[:500])
    else:
        print("  Not found")

    # 재생 버튼 클릭 후 다시 확인
    print("\n[4] Clicking play button...")
    play_btn = await page.query_selector('div[aria-label="Play"]')
    if play_btn:
        await play_btn.click(force=True)
        await page.wait_for_timeout(5000)

        # 재생 후 JWPlayer 상태
        jw_after = await page.evaluate("""() => {
            if (typeof jwplayer === 'undefined') return null;
            try {
                const player = jwplayer();
                return {
                    state: player.getState ? player.getState() : null,
                    playlist: player.getPlaylist ? player.getPlaylist() : null,
                    currentItem: player.getPlaylistItem ? player.getPlaylistItem() : null
                };
            } catch(e) {
                return {error: e.message};
            }
        }""")

        print("\n=== JWPlayer After Play Click ===")
        print(json.dumps(jw_after, indent=2, ensure_ascii=False)[:1500])

    # 결과 저장
    result = {
        "jw_info": jw_info,
        "window_keys": window_keys,
        "next_data_exists": next_data is not None,
        "preloaded_exists": preloaded is not None
    }

    with open(OUTPUT_DIR / "page_config.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n[OK] Config saved to {OUTPUT_DIR / 'page_config.json'}")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
