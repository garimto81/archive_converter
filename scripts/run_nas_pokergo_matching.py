"""
NAS-PokerGO 자동 매칭 스크립트

매칭 전략:
1. 연도 기반 필터링
2. 이벤트 번호 추출 및 매칭
3. 제목 유사도 (fuzzy matching)
"""

import re
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"


def extract_event_number(text: str) -> int | None:
    """텍스트에서 이벤트 번호 추출"""
    # Event #13, Event #3, EV-21, ev-17 등
    patterns = [
        r"Event\s*#?\s*(\d+)",
        r"EV[_-]?(\d+)",
        r"#(\d+)\s+\$",
        r"ev[_-](\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_buyin(text: str) -> str | None:
    """텍스트에서 바이인 추출"""
    # $5K, $25K, $10,000, $1.5K 등
    patterns = [
        r"\$(\d+(?:,\d+)?(?:\.\d+)?)[Kk]",  # $5K, $1.5K
        r"\$(\d{1,3}(?:,\d{3})+)",  # $10,000
        r"\$(\d+)",  # $500
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def normalize_title(text: str) -> str:
    """제목 정규화 (비교용)"""
    # 소문자 변환
    text = text.lower()
    # 특수문자 제거
    text = re.sub(r"[^\w\s]", " ", text)
    # 공백 정규화
    text = re.sub(r"\s+", " ", text).strip()
    # 일반적인 단어 제거
    stopwords = ["the", "a", "an", "and", "or", "of", "to", "in", "for", "on", "at"]
    words = [w for w in text.split() if w not in stopwords]
    return " ".join(words)


def calculate_similarity(s1: str, s2: str) -> float:
    """두 문자열의 유사도 계산 (0.0 - 1.0)"""
    return SequenceMatcher(None, s1, s2).ratio()


def match_by_event_number(asset: dict, pokergo_videos: list) -> list:
    """이벤트 번호로 매칭"""
    matches = []

    asset_event = extract_event_number(asset["file_name"])
    if not asset_event:
        return matches

    asset_year = asset["year"]

    for video in pokergo_videos:
        video_event = extract_event_number(video["title"])
        video_year = video["year"]

        # 연도 + 이벤트 번호 매칭
        if asset_year == video_year and asset_event == video_event:
            confidence = 0.9  # 높은 신뢰도

            # 바이인도 일치하면 신뢰도 더 높임
            asset_buyin = extract_buyin(asset["file_name"])
            video_buyin = extract_buyin(video["title"])
            if asset_buyin and video_buyin and asset_buyin == video_buyin:
                confidence = 0.95

            matches.append({
                "video_id": video["video_id"],
                "match_type": "event_number",
                "confidence": confidence,
                "reason": f"Year={asset_year}, Event #{asset_event}"
            })

    return matches


def match_by_title_similarity(asset: dict, pokergo_videos: list, threshold: float = 0.5) -> list:
    """제목 유사도로 매칭"""
    matches = []

    asset_normalized = normalize_title(asset["file_name"])
    asset_year = asset["year"]

    for video in pokergo_videos:
        # 같은 연도만
        if video["year"] != asset_year:
            continue

        video_normalized = normalize_title(video["title"])
        similarity = calculate_similarity(asset_normalized, video_normalized)

        if similarity >= threshold:
            matches.append({
                "video_id": video["video_id"],
                "match_type": "title_similarity",
                "confidence": round(similarity, 3),
                "reason": f"Similarity={similarity:.1%}"
            })

    # 유사도 높은 순 정렬
    matches.sort(key=lambda x: x["confidence"], reverse=True)
    return matches[:3]  # 상위 3개만


def run_matching():
    """매칭 실행"""
    print("=" * 60)
    print("NAS-PokerGO Auto Matching")
    print("=" * 60)

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 기존 매칭 삭제
    cursor.execute("DELETE FROM nas_pokergo_matches")
    print(f"Cleared existing matches")

    # NAS Assets 조회 (WSOP만)
    cursor.execute("""
        SELECT asset_uuid, file_name, year, event_number, brand
        FROM assets
        WHERE brand = 'WSOP' AND year IS NOT NULL
    """)
    assets = [dict(row) for row in cursor.fetchall()]
    print(f"NAS Assets to match: {len(assets)}")

    # PokerGO Videos 조회
    cursor.execute("""
        SELECT video_id, title, year, duration_sec
        FROM pokergo_videos
        WHERE brand = 'WSOP'
    """)
    pokergo_videos = [dict(row) for row in cursor.fetchall()]
    print(f"PokerGO Videos: {len(pokergo_videos)}")

    # 매칭 실행
    total_matches = 0
    matched_assets = set()

    print("\nMatching...")

    for i, asset in enumerate(assets):
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(assets)} processed...")

        best_match = None

        # 1차: 이벤트 번호 매칭
        event_matches = match_by_event_number(asset, pokergo_videos)
        if event_matches:
            best_match = event_matches[0]

        # 2차: 제목 유사도 매칭 (이벤트 번호 매칭 실패 시)
        if not best_match:
            similarity_matches = match_by_title_similarity(asset, pokergo_videos, threshold=0.6)
            if similarity_matches:
                best_match = similarity_matches[0]

        # 매칭 결과 저장
        if best_match:
            cursor.execute("""
                INSERT INTO nas_pokergo_matches
                (asset_uuid, pokergo_video_id, match_type, match_confidence, match_reason)
                VALUES (?, ?, ?, ?, ?)
            """, (
                asset["asset_uuid"],
                best_match["video_id"],
                best_match["match_type"],
                best_match["confidence"],
                best_match["reason"]
            ))

            # Asset 업데이트
            cursor.execute("""
                UPDATE assets SET pokergo_matched = 1 WHERE asset_uuid = ?
            """, (asset["asset_uuid"],))

            # PokerGO 업데이트
            cursor.execute("""
                UPDATE pokergo_videos
                SET nas_matched = 1, matched_asset_uuid = ?, match_confidence = ?
                WHERE video_id = ?
            """, (asset["asset_uuid"], best_match["confidence"], best_match["video_id"]))

            total_matches += 1
            matched_assets.add(asset["asset_uuid"])

    conn.commit()

    # 결과 통계
    print("\n" + "=" * 60)
    print("Matching Complete!")
    print("=" * 60)
    print(f"Total Matches: {total_matches}")
    print(f"Matched Assets: {len(matched_assets)}/{len(assets)} ({100*len(matched_assets)/len(assets):.1f}%)")

    # 매칭 타입별 통계
    cursor.execute("""
        SELECT match_type, COUNT(*) as cnt, AVG(match_confidence) as avg_conf
        FROM nas_pokergo_matches
        GROUP BY match_type
    """)
    print("\nMatch Type Statistics:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} (avg confidence: {row[2]:.2f})")

    # 연도별 매칭 통계
    cursor.execute("""
        SELECT a.year, COUNT(*) as matched
        FROM nas_pokergo_matches m
        JOIN assets a ON m.asset_uuid = a.asset_uuid
        GROUP BY a.year
        ORDER BY a.year DESC
    """)
    print("\nMatches by Year:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    run_matching()
