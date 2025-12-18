"""
NAS-PokerGO Matching v2
- Event# + Day/Final 구분 매칭
- 중복 PokerGO 영상 처리 (같은 title, 다른 show)
"""

import re
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path

PROJECT_ROOT = Path(r"D:\AI\claude01\Archive_Converter")
UNIFIED_DB = PROJECT_ROOT / "data" / "unified_archive.db"
POKERGO_DB = PROJECT_ROOT / "data" / "pokergo" / "pokergo.db"


def extract_event_number(text: str) -> str:
    """Event# 추출"""
    patterns = [
        r"Event\s*#\s*(\d+)",
        r"EV[_-]?(\d+)",
        r"#(\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1)
    return ""


def extract_day_info(text: str, path: str = "") -> str:
    """Day 정보 추출 - Day N, Final, Part N 등"""
    combined = text + " " + path

    # Final Table 먼저 체크
    if re.search(r"FINAL\s*TABLE", combined, re.IGNORECASE):
        return "FINAL"
    if re.search(r"\bFinal\b", combined, re.IGNORECASE) and "Day" not in combined:
        return "FINAL"

    # Day N 패턴
    m = re.search(r"Day\s*(\d+[A-D]?)", combined, re.IGNORECASE)
    if m:
        day = m.group(1).upper()
        # Part 정보도 추출
        part_m = re.search(r"Part\s*(\d+)", combined, re.IGNORECASE)
        if part_m:
            return f"Day{day}_Part{part_m.group(1)}"
        return f"Day{day}"

    # Day 없으면 Final로 간주 (Event 파일)
    if extract_event_number(text):
        return "FINAL"

    return ""


def similarity(a: str, b: str) -> float:
    """문자열 유사도"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def main():
    print("=" * 80)
    print("NAS-PokerGO Matching v2 - Event# + Day/Final")
    print("=" * 80)

    conn = sqlite3.connect(str(UNIFIED_DB))
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    pg_conn = sqlite3.connect(str(POKERGO_DB))
    pg_conn.row_factory = sqlite3.Row
    pg_c = pg_conn.cursor()

    # 기존 매칭 클리어
    c.execute("DELETE FROM nas_pokergo_matches")
    c.execute("UPDATE assets SET pokergo_matched = 0")
    c.execute("UPDATE pokergo_videos SET nas_matched = 0")
    conn.commit()

    # PokerGO 영상 로드 (unique title만)
    pg_c.execute("""
        SELECT id, title, show, year
        FROM videos
        WHERE year >= 2020
        ORDER BY title
    """)

    # title 기준 중복 제거 (첫 번째만 사용)
    pg_videos = {}
    for row in pg_c.fetchall():
        title = row['title']
        if title not in pg_videos:
            pg_videos[title] = {
                'id': row['id'],
                'title': title,
                'show': row['show'],
                'year': row['year'],
                'event_num': extract_event_number(title),
                'day_info': extract_day_info(title),
            }

    print(f"Loaded {len(pg_videos)} unique PokerGO videos")

    # NAS 파일 로드
    c.execute("""
        SELECT asset_uuid, file_name, relative_path, year, brand
        FROM assets
        WHERE brand = 'WSOP' AND year >= 2020
    """)
    nas_files = c.fetchall()
    print(f"Loaded {len(nas_files)} NAS files")

    # 매칭 실행
    matches = []
    matched_count = 0

    for nas in nas_files:
        fname = nas['file_name']
        path = nas['relative_path'] or ""
        nas_event = extract_event_number(fname + " " + path)
        nas_day = extract_day_info(fname, path)

        best_match = None
        best_score = 0
        match_type = ""

        for title, pg in pg_videos.items():
            # 연도 체크
            if pg['year'] != nas['year']:
                continue

            score = 0

            # 전략 1: Event# + Day 매칭 (Bracelet Events)
            if nas_event and pg['event_num'] == nas_event:
                # Day 매칭
                day_match_score = 0
                if nas_day and pg['day_info']:
                    if nas_day == pg['day_info']:
                        day_match_score = 1.0
                    elif nas_day == "FINAL" and pg['day_info'] == "FINAL":
                        day_match_score = 1.0
                    elif "Day" in nas_day and "Day" in pg['day_info']:
                        nas_day_num = re.search(r"Day(\d+)", nas_day)
                        pg_day_num = re.search(r"Day(\d+)", pg['day_info'])
                        if nas_day_num and pg_day_num:
                            if nas_day_num.group(1) == pg_day_num.group(1):
                                day_match_score = 0.9
                elif not nas_day and not pg['day_info']:
                    day_match_score = 0.8

                if day_match_score > 0:
                    title_sim = similarity(fname, pg['title'])
                    score = (day_match_score * 0.6) + (title_sim * 0.4)
                    if score > best_score:
                        best_score = score
                        best_match = pg
                        match_type = "event_day"

            # 전략 2: Title Similarity (Main Event 등 Event# 없는 경우)
            elif not nas_event and "Main Event" in fname and "Main Event" in pg['title']:
                # Day 정보 비교
                nas_day_clean = nas_day.replace("_", " ")
                pg_day_clean = pg['day_info'].replace("_", " ")

                if nas_day_clean and pg_day_clean:
                    # 정확한 Day 매칭
                    if nas_day_clean == pg_day_clean:
                        title_sim = similarity(fname, pg['title'])
                        if title_sim > 0.7:
                            score = title_sim
                            if score > best_score:
                                best_score = score
                                best_match = pg
                                match_type = "title_similarity"

        if best_match and best_score >= 0.5:
            matches.append({
                'asset_uuid': nas['asset_uuid'],
                'pokergo_video_id': best_match['id'],
                'match_type': match_type,
                'match_confidence': best_score,
                'nas_file': fname,
                'pg_title': best_match['title'],
                'nas_day': nas_day,
                'pg_day': best_match['day_info'],
            })
            matched_count += 1

    print(f"\nMatched: {matched_count} files")

    # DB에 저장
    for m in matches:
        c.execute("""
            INSERT OR REPLACE INTO nas_pokergo_matches
            (asset_uuid, pokergo_video_id, match_type, match_confidence)
            VALUES (?, ?, ?, ?)
        """, (m['asset_uuid'], m['pokergo_video_id'], m['match_type'], m['match_confidence']))

        c.execute("UPDATE assets SET pokergo_matched = 1 WHERE asset_uuid = ?", (m['asset_uuid'],))

    # PokerGO matched 업데이트
    c.execute("""
        UPDATE pokergo_videos SET nas_matched = 1
        WHERE video_id IN (SELECT pokergo_video_id FROM nas_pokergo_matches)
    """)

    conn.commit()

    # 결과 출력
    print("\n" + "=" * 80)
    print("MATCHING RESULTS BY DAY TYPE")
    print("=" * 80)

    day_stats = {}
    for m in matches:
        key = f"{m['nas_day']} -> {m['pg_day']}"
        if key not in day_stats:
            day_stats[key] = 0
        day_stats[key] += 1

    for key, count in sorted(day_stats.items()):
        print(f"  {key}: {count}")

    # 샘플 출력
    print("\n" + "=" * 80)
    print("SAMPLE MATCHES (FINAL)")
    print("=" * 80)

    final_matches = [m for m in matches if m['nas_day'] == 'FINAL'][:5]
    for m in final_matches:
        print(f"NAS: {m['nas_file'][:60]}")
        print(f" -> PG: {m['pg_title'][:60]}")
        print(f"    Day: {m['nas_day']} -> {m['pg_day']}, Score: {m['match_confidence']:.2f}")
        print()

    conn.close()
    pg_conn.close()

    print("Done!")


if __name__ == "__main__":
    main()
