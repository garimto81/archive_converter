"""
NAS 파일 중복 그룹화 및 Primary/Child 분류
동일 콘텐츠 파일들을 그룹화하고 대표 파일 선정

Usage:
    python scripts/group_duplicate_content.py
    python scripts/group_duplicate_content.py --folder "WSOP 1973"  # 특정 폴더만
"""

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileInfo:
    """파일 정보"""
    id: int
    filename: str
    path: str
    folder: str
    extension: str
    size_bytes: int
    year: int
    brand: str
    event_type: str
    episode: int
    duration_sec: float
    resolution: str
    bitrate: int
    video_codec: str


@dataclass
class ContentGroup:
    """콘텐츠 그룹"""
    id: int
    natural_title: str
    brand: str
    year: int
    event_type: str
    episode: int
    duration_sec: float
    primary_file: FileInfo
    children: list[FileInfo]
    file_count: int


class DuplicateGrouper:
    """중복 파일 그룹화 클래스"""

    # Primary 선정 점수
    KEYWORD_SCORES = {
        "nobug": 100,
        "clean": 100,
        "final": 80,
        "master": 80,
        "mastered": 80,
    }

    FORMAT_SCORES = {
        "mp4": 50,
        "mov": 40,
        "mxf": 30,
        "avi": 10,
    }

    RESOLUTION_SCORES = {
        "1920": 30,  # 1080p
        "1280": 25,  # 720p
        "720": 20,   # SD Wide
        "640": 10,   # SD
    }

    def __init__(self, db_path: str = "data/nas_footage.db"):
        self.db_path = db_path
        self.groups: list[ContentGroup] = []

    def load_files(self, folder_filter: str = None) -> list[FileInfo]:
        """DB에서 파일 목록 로드"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # classified_files가 nas_classified.db에 있으므로 기본값 사용
        query = """
            SELECT
                f.id, f.filename, f.path, f.folder, f.extension,
                f.size_bytes, f.year, f.brand,
                COALESCE(f.asset_type, 'MAIN_EVENT') as event_type,
                0 as episode,
                f.duration_sec, f.resolution, f.bitrate, f.video_codec
            FROM files f
            WHERE f.duration_sec IS NOT NULL
        """

        params = []
        if folder_filter:
            query += " AND f.path LIKE ?"
            params.append(f"%{folder_filter}%")

        query += " ORDER BY f.year DESC, f.folder, f.filename"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        files = []
        for row in rows:
            files.append(FileInfo(
                id=row[0],
                filename=row[1],
                path=row[2],
                folder=row[3],
                extension=row[4] or "",
                size_bytes=row[5] or 0,
                year=row[6],
                brand=row[7] or "WSOP",
                event_type=row[8],
                episode=row[9] or 0,
                duration_sec=row[10] or 0,
                resolution=row[11] or "",
                bitrate=row[12] or 0,
                video_codec=row[13] or "",
            ))

        return files

    def is_same_content(self, file_a: FileInfo, file_b: FileInfo) -> bool:
        """동일 콘텐츠 여부 판단"""
        # 1. 같은 연도 필수
        if file_a.year != file_b.year:
            return False

        # 2. 같은 폴더면 높은 확률
        same_folder = file_a.folder == file_b.folder

        # 3. 재생 시간 유사성 체크
        if file_a.duration_sec and file_b.duration_sec:
            duration_diff = abs(file_a.duration_sec - file_b.duration_sec)
            max_duration = max(file_a.duration_sec, file_b.duration_sec)

            # 같은 폴더: 5% 허용 (또는 최소 60초)
            # 다른 폴더: 2% 허용 (또는 최소 30초)
            if same_folder:
                threshold = max(max_duration * 0.05, 60)
            else:
                threshold = max(max_duration * 0.02, 30)

            if duration_diff > threshold:
                return False

        # 4. 같은 폴더 + 같은 연도면 대부분 동일 콘텐츠
        # (episode 체크는 다른 폴더일 때만 적용)
        if not same_folder:
            if file_a.episode and file_b.episode:
                if file_a.episode != file_b.episode:
                    return False

            # 다른 폴더면 이벤트 타입도 체크
            if file_a.event_type != file_b.event_type:
                return False

        return True

    def calculate_primary_score(self, file: FileInfo) -> int:
        """Primary 선정 점수 계산"""
        score = 0
        filename_lower = file.filename.lower()

        # 키워드 점수
        for keyword, pts in self.KEYWORD_SCORES.items():
            if keyword in filename_lower:
                score += pts
                break  # 하나만 적용

        # 포맷 점수
        ext = file.extension.lower().lstrip(".")
        score += self.FORMAT_SCORES.get(ext, 0)

        # 해상도 점수
        if file.resolution:
            width = file.resolution.split("x")[0] if "x" in file.resolution else ""
            for res_key, pts in self.RESOLUTION_SCORES.items():
                if width.startswith(res_key[:3]):
                    score += pts
                    break

        # 비트레이트 점수 (정규화, 최대 20점)
        if file.bitrate:
            bitrate_score = min(file.bitrate / 1000000, 20)
            score += bitrate_score

        # 파일 크기 점수 (같은 포맷 내에서, 최대 10점)
        if file.size_bytes:
            size_score = min(file.size_bytes / (1024 * 1024 * 1024), 10)  # GB 기준
            score += size_score

        return int(score)

    def group_files(self, files: list[FileInfo]) -> list[ContentGroup]:
        """파일들을 콘텐츠 그룹으로 분류"""
        groups = []
        processed = set()
        group_id = 0

        for i, file_a in enumerate(files):
            if file_a.id in processed:
                continue

            # 새 그룹 시작
            group_files = [file_a]
            processed.add(file_a.id)

            # 동일 콘텐츠 찾기
            for j, file_b in enumerate(files):
                if i == j or file_b.id in processed:
                    continue

                if self.is_same_content(file_a, file_b):
                    group_files.append(file_b)
                    processed.add(file_b.id)

            # Primary 선정
            scored_files = [(f, self.calculate_primary_score(f)) for f in group_files]
            scored_files.sort(key=lambda x: x[1], reverse=True)

            primary = scored_files[0][0]
            children = [f for f, _ in scored_files[1:]]

            group_id += 1

            # Natural Title 생성
            natural_title = self._generate_title(primary)

            groups.append(ContentGroup(
                id=group_id,
                natural_title=natural_title,
                brand=primary.brand,
                year=primary.year,
                event_type=primary.event_type,
                episode=primary.episode,
                duration_sec=primary.duration_sec,
                primary_file=primary,
                children=children,
                file_count=len(group_files),
            ))

        return groups

    def _generate_title(self, file: FileInfo) -> str:
        """자연스러운 제목 생성"""
        parts = []

        # Brand
        brand_map = {
            "WSOP": "WSOP",
            "WSOPE": "WSOP Europe",
            "WSOPP": "WSOP Paradise",
            "WSOPC": "WSOP Circuit",
            "PAD": "Poker After Dark",
        }
        parts.append(brand_map.get(file.brand, file.brand))

        # Year
        if file.year:
            parts.append(str(file.year))

        # Event Type
        event_map = {
            "ME": "Main Event",
            "BE": "Bracelet Event",
            "HR": "High Roller",
            "TOC": "Tournament of Champions",
        }
        parts.append(event_map.get(file.event_type, file.event_type))

        # Episode
        if file.episode:
            parts.append(f"- Episode {file.episode}")

        return " ".join(parts)

    def save_to_db(self, groups: list[ContentGroup]):
        """그룹 결과를 DB에 저장"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS content_groups (
                id INTEGER PRIMARY KEY,
                natural_title TEXT NOT NULL,
                brand TEXT,
                year INTEGER,
                event_type TEXT,
                episode INTEGER,
                duration_sec REAL,
                primary_file_id INTEGER REFERENCES files(id),
                file_count INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS file_group_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id INTEGER REFERENCES files(id),
                group_id INTEGER REFERENCES content_groups(id),
                is_primary INTEGER DEFAULT 0,
                primary_score INTEGER,
                role TEXT,
                UNIQUE(file_id, group_id)
            )
        """)

        # 기존 데이터 삭제
        cur.execute("DELETE FROM file_group_mapping")
        cur.execute("DELETE FROM content_groups")

        # 그룹 저장
        for group in groups:
            cur.execute("""
                INSERT INTO content_groups (
                    id, natural_title, brand, year, event_type,
                    episode, duration_sec, primary_file_id, file_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                group.id,
                group.natural_title,
                group.brand,
                group.year,
                group.event_type,
                group.episode,
                group.duration_sec,
                group.primary_file.id,
                group.file_count,
            ))

            # Primary 파일 매핑
            primary_score = self.calculate_primary_score(group.primary_file)
            cur.execute("""
                INSERT INTO file_group_mapping (
                    file_id, group_id, is_primary, primary_score, role
                ) VALUES (?, ?, 1, ?, 'PRIMARY')
            """, (group.primary_file.id, group.id, primary_score))

            # Child 파일 매핑
            for child in group.children:
                child_score = self.calculate_primary_score(child)
                # 역할 결정
                if child.extension.lower() != group.primary_file.extension.lower():
                    role = "ALTERNATE_FORMAT"
                else:
                    role = "BACKUP"

                cur.execute("""
                    INSERT INTO file_group_mapping (
                        file_id, group_id, is_primary, primary_score, role
                    ) VALUES (?, ?, 0, ?, ?)
                """, (child.id, group.id, child_score, role))

        conn.commit()
        conn.close()

    def save_to_json(self, groups: list[ContentGroup], output_path: str):
        """그룹 결과를 JSON으로 저장"""
        data = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "total_groups": len(groups),
            "total_files": sum(g.file_count for g in groups),
            "statistics": {
                "single_file_groups": sum(1 for g in groups if g.file_count == 1),
                "multi_file_groups": sum(1 for g in groups if g.file_count > 1),
                "total_children": sum(len(g.children) for g in groups),
            },
            "groups": []
        }

        for group in groups:
            group_data = {
                "id": group.id,
                "natural_title": group.natural_title,
                "brand": group.brand,
                "year": group.year,
                "event_type": group.event_type,
                "episode": group.episode,
                "duration_sec": group.duration_sec,
                "file_count": group.file_count,
                "primary": {
                    "id": group.primary_file.id,
                    "filename": group.primary_file.filename,
                    "path": group.primary_file.path,
                    "resolution": group.primary_file.resolution,
                    "score": self.calculate_primary_score(group.primary_file),
                },
                "children": [
                    {
                        "id": c.id,
                        "filename": c.filename,
                        "role": "ALTERNATE_FORMAT" if c.extension != group.primary_file.extension else "BACKUP",
                        "score": self.calculate_primary_score(c),
                    }
                    for c in group.children
                ]
            }
            data["groups"].append(group_data)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Group duplicate NAS files")
    parser.add_argument("--db", default="data/nas_footage.db", help="Database path")
    parser.add_argument("--folder", help="Filter by folder name")
    parser.add_argument("--output", default="data/content_groups.json", help="Output JSON path")
    args = parser.parse_args()

    print("=" * 60)
    print("NAS Duplicate Content Grouper")
    print("=" * 60)

    grouper = DuplicateGrouper(args.db)

    # 파일 로드
    print("\nLoading files from database...")
    files = grouper.load_files(args.folder)
    print(f"  Loaded {len(files)} files with media info")

    if not files:
        print("No files with media information. Run scan_nas_media_info.py first.")
        return

    # 그룹화 실행
    print("\nGrouping files by content...")
    groups = grouper.group_files(files)

    # 통계
    single_groups = sum(1 for g in groups if g.file_count == 1)
    multi_groups = sum(1 for g in groups if g.file_count > 1)
    total_children = sum(len(g.children) for g in groups)

    print(f"\n{'='*60}")
    print("Grouping Results")
    print(f"{'='*60}")
    print(f"  Total Groups: {len(groups)}")
    print(f"  Single-file Groups: {single_groups}")
    print(f"  Multi-file Groups: {multi_groups}")
    print(f"  Total Children (Backups): {total_children}")

    # 중복 그룹 샘플 출력
    print(f"\n{'='*60}")
    print("Sample Multi-file Groups")
    print(f"{'='*60}")

    multi_file_groups = [g for g in groups if g.file_count > 1][:5]
    for group in multi_file_groups:
        print(f"\n[Group {group.id}] {group.natural_title}")
        print(f"  Files: {group.file_count}")
        print(f"  Duration: {group.duration_sec:.1f}s")
        primary_score = grouper.calculate_primary_score(group.primary_file)
        print(f"  PRIMARY: {group.primary_file.filename} (score: {primary_score})")
        for child in group.children:
            child_score = grouper.calculate_primary_score(child)
            role = "ALT_FMT" if child.extension != group.primary_file.extension else "BACKUP"
            print(f"    CHILD: {child.filename} ({role}, score: {child_score})")

    # 저장
    print(f"\nSaving to database...")
    grouper.save_to_db(groups)
    print(f"  Saved to {args.db}")

    print(f"\nSaving to JSON...")
    grouper.save_to_json(groups, args.output)
    print(f"  Saved to {args.output}")


if __name__ == "__main__":
    main()
