"""
PokerGO 배치 파일 병합

여러 배치로 수집된 pokergo_details_*.json 파일들을 하나로 병합합니다.
"""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "pokergo"


def merge_batch_files():
    """배치 파일들을 하나로 병합"""
    # 최근 생성된 details 파일들 찾기 (오늘 날짜)
    today = datetime.now().strftime('%Y%m%d')
    files = sorted(DATA_DIR.glob(f"pokergo_details_{today}_*.json"))

    if not files:
        print("[ERROR] 병합할 파일이 없습니다")
        return None

    print(f"[INFO] {len(files)}개 배치 파일 발견:")
    for f in files:
        print(f"  - {f.name}")

    # 모든 비디오 병합
    all_videos = []
    seen_urls = set()

    for file_path in files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        videos = data.get("videos", [])
        for video in videos:
            url = video.get("url", "")
            if url and url not in seen_urls:
                all_videos.append(video)
                seen_urls.add(url)

        print(f"  → {file_path.name}: {len(videos)}개 비디오")

    # 병합된 파일 저장
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = DATA_DIR / f"pokergo_merged_{timestamp}.json"

    output_data = {
        "scraped_at": datetime.now().isoformat(),
        "total_videos": len(all_videos),
        "source_files": [f.name for f in files],
        "videos": all_videos,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"[SUCCESS] 병합 완료!")
    print(f"{'='*60}")
    print(f"  출력 파일: {output_file}")
    print(f"  총 비디오 수: {len(all_videos)}개")

    # 통계
    titles_count = sum(1 for v in all_videos if v.get("title"))
    desc_count = sum(1 for v in all_videos if v.get("description"))
    show_count = sum(1 for v in all_videos if v.get("show_name"))
    event_count = sum(1 for v in all_videos if v.get("event"))

    print(f"\n[통계]")
    print(f"  - 제목 있음: {titles_count}개")
    print(f"  - 설명 있음: {desc_count}개")
    print(f"  - 쇼 정보 있음: {show_count}개")
    print(f"  - 이벤트 정보 있음: {event_count}개")

    return output_file


if __name__ == "__main__":
    print("=" * 60)
    print("PokerGO 배치 파일 병합기")
    print("=" * 60)

    merge_batch_files()
