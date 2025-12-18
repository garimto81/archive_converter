"""
NAS 파일 분류 스크립트
모든 NAS 파일을 자연스러운 제목과 카테고리로 분류

Usage:
    python scripts/classify_nas_files.py
"""

import json
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ClassifiedFile:
    """분류된 파일 레코드"""

    id: int
    original_filename: str
    original_path: str
    natural_title: str
    brand: str
    year: int | None
    event_type: str
    event_num: int | None
    day_or_episode: int | None
    day_type: str | None  # 'day' or 'episode'
    game_type: str
    content_type: str
    confidence: float
    parse_method: str


class NASFileClassifier:
    """NAS 파일 분류기"""

    # 브랜드 매핑
    BRAND_MAP = {
        "WSOPE": "WSOP Europe",
        "WSOPP": "WSOP Paradise",
        "WSOPC": "WSOP Circuit",
        "WSOP": "WSOP",
        "PAD": "Poker After Dark",
        "HCL": "Hustler Casino Live",
        "GOG": "Game of Gold",
        "GGM": "GG Millions",
        "GGP": "GGPoker",
        "MPP": "Mystery Poker Pro",
    }

    # 이벤트 타입 매핑
    EVENT_TYPE_MAP = {
        "ME": "Main Event",
        "BE": "Bracelet Event",
        "HR": "High Roller",
        "MB": "Mystery Bounty",
        "CG": "Cash Game",
        "TOC": "Tournament of Champions",
        "SE": "Side Event",
    }

    # 게임 타입 매핑
    GAME_TYPE_MAP = {
        "NLH": "No Limit Hold'em",
        "PLO": "Pot Limit Omaha",
        "HORSE": "HORSE",
        "STUD": "Seven Card Stud",
        "RAZZ": "Razz",
        "27": "2-7 Triple Draw",
    }

    def __init__(self, db_path: str = "data/nas_footage.db"):
        self.db_path = db_path
        self.patterns = self._compile_patterns()

    def _compile_patterns(self) -> list[tuple[str, re.Pattern, str]]:
        """파일명 파싱 패턴 컴파일"""
        patterns = [
            # NEW: GGPoker/PokerOK Tournament Format
            (
                "ggpoker_gtd",
                re.compile(
                    r"\$[\d.]+[MK]?\s+GTD.*?Day\s*(\d+\w?)",
                    re.IGNORECASE,
                ),
                "GGP",
            ),
            # NEW: WSOP 2025 Bracelet Event
            (
                "wsop_2025_be",
                re.compile(
                    r"WSOP\s+(\d{4})\s+(?:Bracelet\s+)?Event[s]?\s*[#_]?\s*(\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # NEW: N_YYYY WSOPE Format
            (
                "wsope_2025",
                re.compile(
                    r"(\d+)[_-](\d{4})\s+WSOPE?\s*[#]?(\d+)",
                    re.IGNORECASE,
                ),
                "WSOPE",
            ),
            # NEW: WSOP Super Circuit
            (
                "wsop_circuit",
                re.compile(
                    r"WSOP\s+Super\s+Circuit.*?Day\s*(\d+\w?)",
                    re.IGNORECASE,
                ),
                "WSOPC",
            ),
            # NEW: WSOPE YYYY format with BE#
            (
                "wsope_be",
                re.compile(
                    r"WSOPE?\s*_?\s*(\d{4})[_\s]+.*?(?:BRACELET|BE)[_\s]*(?:EVENT)?[_\s#]*(\d+)",
                    re.IGNORECASE,
                ),
                "WSOPE",
            ),
            # NEW: Hand Clip folder pattern
            (
                "hand_clip",
                re.compile(
                    r"Hand\s*Clip.*?Day\s*(\d+\w?)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # NEW: WSOP-LAS VEGAS streaming
            (
                "wsop_lv_stream",
                re.compile(
                    r"WSOP[\s_-]*(?:LAS[\s_]*VEGAS|LV).*?(\d{4})",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 1. WSOP Paradise 2023-2025
            (
                "paradise",
                re.compile(
                    r"WSOP Paradise[_ ](.+?)[_ ]-[_ ](.+?)\.mp4",
                    re.IGNORECASE,
                ),
                "WSOPP",
            ),
            # 2. WSOP Europe 2024 Format
            (
                "wsope_2024",
                re.compile(
                    r"#?WSOPE?[_ ]+(\d{4})[_ ]+(.+?)[_ ]+DAY[_ ]+(\d+\w?)",
                    re.IGNORECASE,
                ),
                "WSOPE",
            ),
            # 3. WSOP Europe Episode Format
            (
                "wsope_episode",
                re.compile(
                    r"WSOPE?Y?(\d{2})[_-]Episode[_-](\d+)",
                    re.IGNORECASE,
                ),
                "WSOPE",
            ),
            # 4. Modern WSOP Episode Format (2020+)
            (
                "wsop_episode_modern",
                re.compile(
                    r"WSOP[_ ]+(\d{4})[_ ]+Main Event[_ ]+[_|][_ ]+Episode[_ ]+(\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 5. Mastered MOV Format (2009-2016)
            (
                "mastered_mov",
                re.compile(
                    r"\.?_?WSOP(\d{2})[_-]ME(\d{2})[_-]FINAL",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 6. YYYY WSOP ME Format (2009-2012)
            (
                "yyyy_wsop_me",
                re.compile(
                    r"\.?_?(\d{4})[_ ]+WSOP[_ ]+ME(\d{2})",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 7. ESPN Show Format (2005-2008)
            (
                "espn_show",
                re.compile(
                    r"ESPN[_ ]+(\d{4})[_ ]+WSOP[_ ]+SEASON[_ ]+(\d+)[_ ]+SHOW[_ ]+(\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 8. WSOP YYYY Show Format (2005-2008)
            (
                "wsop_show",
                re.compile(
                    r"WSOP[_ ]+(\d{4})[_ ]+Show[_ ]+(\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 9. MXF Format (2003-2004)
            (
                "mxf_format",
                re.compile(
                    r"WSOP[_-](\d{4})[_-](\d{2})\.mxf",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 10. Classic Format (1973-2002)
            (
                "classic",
                re.compile(
                    r"wsop[_-](\d{4})[_-]me",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 11. Bracelet Event Format
            (
                "bracelet_ev",
                re.compile(
                    r"wsop[_-](\d{4})[_-]ev[_-](\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 12. Bracelet Event Modern (10-wsop-2024-be-ev-21)
            (
                "bracelet_modern",
                re.compile(
                    r"(\d+)[_-]wsop[_-](\d{4})[_-]be[_-]ev[_-](\d+)",
                    re.IGNORECASE,
                ),
                "WSOP",
            ),
            # 13. PAD Format
            (
                "pad",
                re.compile(
                    r"PAD[_-]S(\d+)[_-]EP(\d+)",
                    re.IGNORECASE,
                ),
                "PAD",
            ),
            # 14. HCL Format
            (
                "hcl",
                re.compile(
                    r"HCL[_-]S(\d+)[_-]EP(\d+)",
                    re.IGNORECASE,
                ),
                "HCL",
            ),
            # 15. GOG Format
            (
                "gog",
                re.compile(
                    r"GOG[_-]S(\d+)[_-]EP(\d+)",
                    re.IGNORECASE,
                ),
                "GOG",
            ),
            # 16. GG Millions Format
            (
                "ggm",
                re.compile(
                    r"GGMillion",
                    re.IGNORECASE,
                ),
                "GGM",
            ),
        ]
        return patterns

    def _extract_year_from_path(self, path: str) -> int | None:
        """경로에서 연도 추출"""
        # 폴더 경로에서 WSOP YYYY 패턴 찾기
        match = re.search(r"WSOP[\s_-]+(\d{4})", path, re.IGNORECASE)
        if match:
            return int(match.group(1))

        # 4자리 연도 찾기
        match = re.search(r"(\d{4})", path)
        if match:
            year = int(match.group(1))
            if 1970 <= year <= 2030:
                return year

        return None

    def _extract_day_or_episode(
        self, filename: str, path: str
    ) -> tuple[int | None, str | None]:
        """Day 또는 Episode 번호 추출"""
        # Day 패턴
        day_match = re.search(r"Day[_ ]+(\d+\w?)", filename, re.IGNORECASE)
        if day_match:
            day_str = day_match.group(1)
            # 숫자만 추출 (1A, 1B 등에서)
            day_num = int(re.match(r"\d+", day_str).group())
            return day_num, f"Day {day_str}"

        # Episode 패턴
        ep_match = re.search(r"Episode[_ ]+(\d+)", filename, re.IGNORECASE)
        if ep_match:
            return int(ep_match.group(1)), "Episode"

        # Show 패턴
        show_match = re.search(r"Show[_ ]+(\d+)", filename, re.IGNORECASE)
        if show_match:
            return int(show_match.group(1)), "Episode"

        # ME## 패턴 (ME01, ME02, ...)
        me_match = re.search(r"ME(\d{2})", filename, re.IGNORECASE)
        if me_match:
            return int(me_match.group(1)), "Episode"

        # -## 패턴 (2003-01, 2003-02, ...)
        num_match = re.search(r"-(\d{2})\.(?:mxf|mp4|mov)", filename, re.IGNORECASE)
        if num_match:
            return int(num_match.group(1)), "Episode"

        # 폴더에서 Day 추출
        day_folder = re.search(r"Day[_ ]+(\d+\w?)", path, re.IGNORECASE)
        if day_folder:
            day_str = day_folder.group(1)
            day_num = int(re.match(r"\d+", day_str).group())
            return day_num, f"Day {day_str}"

        return None, None

    def _detect_event_type(self, filename: str, path: str) -> tuple[str, int | None]:
        """이벤트 타입 감지"""
        combined = f"{path}/{filename}".lower()

        # Bracelet Event
        if "bracelet" in combined or "be" in combined or "-ev-" in combined:
            ev_match = re.search(r"ev[_-]?(\d+)", combined)
            ev_num = int(ev_match.group(1)) if ev_match else None
            return "BE", ev_num

        # Main Event
        if "main" in combined or "me" in combined or "main_event" in combined:
            return "ME", None

        # High Roller
        if "high roller" in combined or "hr" in combined:
            return "HR", None

        # Mystery Bounty
        if "mystery" in combined or "bounty" in combined:
            return "MB", None

        # Cash Game
        if "cash" in combined:
            return "CG", None

        # TOC
        if "toc" in combined or "tournament of champions" in combined:
            return "TOC", None

        # Default: Main Event (for pre-2010 archives)
        return "ME", None

    def _detect_game_type(self, filename: str, path: str) -> str:
        """게임 타입 감지"""
        combined = f"{path}/{filename}".lower()

        if "plo" in combined or "omaha" in combined:
            return "PLO"
        if "horse" in combined:
            return "HORSE"
        if "stud" in combined:
            return "STUD"
        if "razz" in combined:
            return "RAZZ"
        if "2-7" in combined or "27" in combined:
            return "27"

        return "NLH"  # Default

    def _detect_content_type(self, filename: str, path: str) -> str:
        """콘텐츠 타입 감지"""
        combined = f"{path}/{filename}".lower()

        if "hand clip" in combined or "handclip" in combined:
            return "HC"
        if "streaming" in combined or "stream" in combined:
            return "ST"
        if "master" in combined or "final" in combined:
            return "MA"
        if "raw" in combined:
            return "RAW"

        return "EP"  # Default: Episode

    def _generate_natural_title(
        self,
        brand: str,
        year: int | None,
        event_type: str,
        event_num: int | None,
        day_episode: int | None,
        day_type: str | None,
        game_type: str,
    ) -> str:
        """자연스러운 제목 생성"""
        parts = []

        # Brand
        brand_name = self.BRAND_MAP.get(brand, brand)
        parts.append(brand_name)

        # Year
        if year:
            parts.append(str(year))

        # Event Type
        event_name = self.EVENT_TYPE_MAP.get(event_type, event_type)
        if event_num:
            event_name = f"{event_name} #{event_num}"
        parts.append(event_name)

        # Day/Episode
        if day_episode and day_type:
            if day_type.startswith("Day"):
                parts.append(f"- {day_type}")
            else:
                parts.append(f"- Episode {day_episode}")

        # Game Type (if not NLH default)
        if game_type != "NLH":
            game_name = self.GAME_TYPE_MAP.get(game_type, game_type)
            parts.append(f"({game_name})")

        return " ".join(parts)

    def classify_file(
        self, file_id: int, filename: str, path: str, year_from_db: int | None
    ) -> ClassifiedFile:
        """단일 파일 분류"""
        brand = "WSOP"  # Default
        year = year_from_db
        event_type = None  # None means not yet determined
        event_num = None
        day_episode = None
        day_type = None
        confidence = 0.5
        parse_method = "default"

        # 패턴 매칭
        for pattern_name, pattern, pattern_brand in self.patterns:
            match = pattern.search(filename)
            if match:
                brand = pattern_brand
                parse_method = pattern_name

                # 패턴별 처리
                if pattern_name == "ggpoker_gtd":
                    day_str = match.group(1)
                    day_episode = int(re.match(r"\d+", day_str).group())
                    day_type = f"Day {day_str}"
                    year = year or self._extract_year_from_path(path)
                    event_type = "ME"
                    brand = "GGP"
                    confidence = 0.85

                elif pattern_name == "wsop_2025_be":
                    year = int(match.group(1))
                    event_num = int(match.group(2))
                    event_type = "BE"
                    confidence = 0.90

                elif pattern_name == "wsope_2025":
                    day_episode = int(match.group(1))
                    year = int(match.group(2))
                    event_num = int(match.group(3))
                    event_type = "BE"
                    day_type = "Episode"
                    confidence = 0.90

                elif pattern_name == "wsop_circuit":
                    day_str = match.group(1)
                    day_episode = int(re.match(r"\d+", day_str).group())
                    day_type = f"Day {day_str}"
                    year = year or self._extract_year_from_path(path)
                    event_type = "ME"
                    confidence = 0.85

                elif pattern_name == "wsope_be":
                    year = int(match.group(1))
                    event_num = int(match.group(2))
                    event_type = "BE"
                    confidence = 0.85

                elif pattern_name == "hand_clip":
                    day_str = match.group(1)
                    day_episode = int(re.match(r"\d+", day_str).group())
                    day_type = f"Day {day_str}"
                    year = year or self._extract_year_from_path(path)
                    confidence = 0.80

                elif pattern_name == "wsop_lv_stream":
                    year = int(match.group(1))
                    confidence = 0.75

                elif pattern_name == "paradise":
                    event_info, day_info = match.groups()
                    year = year or self._extract_year_from_path(path)
                    confidence = 0.85

                elif pattern_name == "wsope_2024":
                    year = int(match.group(1))
                    day_str = match.group(3)
                    day_episode = int(re.match(r"\d+", day_str).group())
                    day_type = f"Day {day_str}"
                    confidence = 0.95

                elif pattern_name == "wsope_episode":
                    year = 2000 + int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    confidence = 0.90

                elif pattern_name == "wsop_episode_modern":
                    year = int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    confidence = 0.95

                elif pattern_name == "mastered_mov":
                    year = 2000 + int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    event_type = "ME"  # ME = Main Event
                    confidence = 0.90

                elif pattern_name == "yyyy_wsop_me":
                    year = int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    event_type = "ME"  # ME = Main Event
                    confidence = 0.90

                elif pattern_name == "espn_show":
                    year = int(match.group(1))
                    day_episode = int(match.group(3))
                    day_type = "Episode"
                    confidence = 0.95

                elif pattern_name == "wsop_show":
                    year = int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    confidence = 0.90

                elif pattern_name == "mxf_format":
                    year = int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    confidence = 0.95

                elif pattern_name == "classic":
                    year = int(match.group(1))
                    confidence = 0.85

                elif pattern_name == "bracelet_ev":
                    year = int(match.group(1))
                    event_num = int(match.group(2))
                    event_type = "BE"
                    confidence = 0.90

                elif pattern_name == "bracelet_modern":
                    day_episode = int(match.group(1))
                    year = int(match.group(2))
                    event_num = int(match.group(3))
                    event_type = "BE"
                    day_type = "Episode"
                    confidence = 0.95

                elif pattern_name in ("pad", "hcl", "gog"):
                    season = int(match.group(1))
                    day_episode = int(match.group(2))
                    day_type = "Episode"
                    # PAD Modern(PokerGO): S7=2020, S13=2023, S14=2024
                    # HCL: S1=2021
                    # GOG: S1=2022
                    if pattern_name == "pad":
                        year = 2010 + season  # PAD S13=2023
                    elif pattern_name == "hcl":
                        year = 2020 + season  # HCL S1=2021
                    else:  # gog
                        year = 2021 + season  # GOG S1=2022
                    confidence = 0.85

                break

        # 연도가 없으면 경로에서 추출
        if not year:
            year = self._extract_year_from_path(path)
            if year and confidence > 0.5:
                confidence = min(confidence, 0.7)

        # Day/Episode 추출 (패턴에서 못 찾은 경우)
        if not day_episode:
            day_episode, day_type = self._extract_day_or_episode(filename, path)
            if day_episode and confidence > 0.5:
                confidence = min(confidence, 0.8)

        # 이벤트 타입 감지 (패턴에서 설정되지 않은 경우에만)
        if event_type is None:
            detected_type, detected_num = self._detect_event_type(filename, path)
            event_type = detected_type
            if detected_num:
                event_num = detected_num

        # 게임/콘텐츠 타입
        game_type = self._detect_game_type(filename, path)
        content_type = self._detect_content_type(filename, path)

        # 자연스러운 제목 생성
        natural_title = self._generate_natural_title(
            brand, year, event_type, event_num, day_episode, day_type, game_type
        )

        return ClassifiedFile(
            id=file_id,
            original_filename=filename,
            original_path=path,
            natural_title=natural_title,
            brand=brand,
            year=year,
            event_type=event_type,
            event_num=event_num,
            day_or_episode=day_episode,
            day_type=day_type.split()[0] if day_type else None,  # 'Day' or 'Episode'
            game_type=game_type,
            content_type=content_type,
            confidence=confidence,
            parse_method=parse_method,
        )

    def classify_all(self) -> list[ClassifiedFile]:
        """모든 파일 분류"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT id, filename, path, year FROM files ORDER BY year DESC, filename")
        rows = cur.fetchall()
        conn.close()

        results = []
        for row in rows:
            file_id, filename, path, year = row
            classified = self.classify_file(file_id, filename, path, year)
            results.append(classified)

        return results

    def save_to_db(self, results: list[ClassifiedFile], output_db: str):
        """분류 결과를 DB에 저장"""
        conn = sqlite3.connect(output_db)
        cur = conn.cursor()

        # 테이블 생성
        cur.execute("""
            CREATE TABLE IF NOT EXISTS classified_files (
                id INTEGER PRIMARY KEY,
                file_id INTEGER,
                original_filename TEXT NOT NULL,
                original_path TEXT,
                natural_title TEXT NOT NULL,
                brand TEXT NOT NULL,
                year INTEGER,
                event_type TEXT,
                event_num INTEGER,
                day_or_episode INTEGER,
                day_type TEXT,
                game_type TEXT DEFAULT 'NLH',
                content_type TEXT,
                confidence REAL DEFAULT 0.0,
                parse_method TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 기존 데이터 삭제
        cur.execute("DELETE FROM classified_files")

        # 데이터 삽입
        for cf in results:
            cur.execute(
                """
                INSERT INTO classified_files (
                    file_id, original_filename, original_path, natural_title,
                    brand, year, event_type, event_num, day_or_episode,
                    day_type, game_type, content_type, confidence, parse_method
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    cf.id,
                    cf.original_filename,
                    cf.original_path,
                    cf.natural_title,
                    cf.brand,
                    cf.year,
                    cf.event_type,
                    cf.event_num,
                    cf.day_or_episode,
                    cf.day_type,
                    cf.game_type,
                    cf.content_type,
                    cf.confidence,
                    cf.parse_method,
                ),
            )

        conn.commit()
        conn.close()

    def save_to_json(self, results: list[ClassifiedFile], output_json: str):
        """분류 결과를 JSON으로 저장"""
        data = {
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "total_files": len(results),
            "statistics": self._calculate_statistics(results),
            "files": [asdict(cf) for cf in results],
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _calculate_statistics(self, results: list[ClassifiedFile]) -> dict:
        """통계 계산"""
        stats = {
            "by_brand": {},
            "by_year": {},
            "by_event_type": {},
            "by_confidence": {"high": 0, "medium": 0, "low": 0},
            "by_parse_method": {},
        }

        for cf in results:
            # Brand
            stats["by_brand"][cf.brand] = stats["by_brand"].get(cf.brand, 0) + 1

            # Year
            year_key = str(cf.year) if cf.year else "Unknown"
            stats["by_year"][year_key] = stats["by_year"].get(year_key, 0) + 1

            # Event Type
            stats["by_event_type"][cf.event_type] = (
                stats["by_event_type"].get(cf.event_type, 0) + 1
            )

            # Confidence
            if cf.confidence >= 0.85:
                stats["by_confidence"]["high"] += 1
            elif cf.confidence >= 0.7:
                stats["by_confidence"]["medium"] += 1
            else:
                stats["by_confidence"]["low"] += 1

            # Parse Method
            stats["by_parse_method"][cf.parse_method] = (
                stats["by_parse_method"].get(cf.parse_method, 0) + 1
            )

        return stats


def main():
    """메인 실행"""
    print("=" * 60)
    print("NAS File Classification")
    print("=" * 60)

    classifier = NASFileClassifier("data/nas_footage.db")

    print("\nClassifying files...")
    results = classifier.classify_all()
    print(f"Total files classified: {len(results)}")

    # DB 저장
    output_db = "data/nas_classified.db"
    classifier.save_to_db(results, output_db)
    print(f"\nSaved to DB: {output_db}")

    # JSON 저장
    output_json = "data/nas_classified.json"
    classifier.save_to_json(results, output_json)
    print(f"Saved to JSON: {output_json}")

    # 통계 출력
    stats = classifier._calculate_statistics(results)

    print("\n" + "=" * 60)
    print("Statistics")
    print("=" * 60)

    print("\nBy Brand:")
    for brand, count in sorted(stats["by_brand"].items(), key=lambda x: -x[1]):
        print(f"  {brand}: {count}")

    print("\nBy Event Type:")
    for etype, count in sorted(stats["by_event_type"].items(), key=lambda x: -x[1]):
        print(f"  {etype}: {count}")

    print("\nBy Confidence:")
    print(f"  High (>=0.85): {stats['by_confidence']['high']}")
    print(f"  Medium (0.7-0.85): {stats['by_confidence']['medium']}")
    print(f"  Low (<0.7): {stats['by_confidence']['low']}")

    print("\nBy Parse Method:")
    for method, count in sorted(stats["by_parse_method"].items(), key=lambda x: -x[1]):
        print(f"  {method}: {count}")

    # 샘플 출력
    print("\n" + "=" * 60)
    print("Sample Classifications")
    print("=" * 60)

    # 연도별 샘플
    sample_years = [2025, 2024, 2020, 2015, 2010, 2005, 2000, 1990]
    for year in sample_years:
        samples = [r for r in results if r.year == year][:2]
        if samples:
            print(f"\n--- {year} ---")
            for s in samples:
                print(f"  Original: {s.original_filename[:60]}...")
                print(f"  Title:    {s.natural_title}")
                print(f"  Conf:     {s.confidence:.2f} ({s.parse_method})")
                print()


if __name__ == "__main__":
    main()
