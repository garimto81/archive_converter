"""SQLite Database Manager"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from contextlib import contextmanager

from ..models.video import Video, VideoStatus


class Database:
    """SQLite database manager for PokerGO Downloader"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "pokergo" / "pokergo.db"
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Videos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    show TEXT NOT NULL,
                    url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    season TEXT,
                    episode TEXT,
                    year INTEGER,
                    duration INTEGER DEFAULT 0,
                    duration_str TEXT,
                    hls_url TEXT,
                    status TEXT DEFAULT 'pending',
                    file_path TEXT,
                    file_size INTEGER DEFAULT 0,
                    progress REAL DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)

            # Config table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # Download queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS download_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'queued',
                    created_at TEXT,
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_show ON videos(show)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_videos_year ON videos(year)")

    # Video CRUD operations
    def insert_video(self, video: Video) -> bool:
        """Insert a new video"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO videos (
                        id, title, show, url, thumbnail_url, season, episode,
                        year, duration, duration_str, hls_url, status, file_path,
                        file_size, progress, error_message, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video.id, video.title, video.show, video.url, video.thumbnail_url,
                    video.season, video.episode, video.year, video.duration,
                    video.duration_str, video.hls_url, video.status.value,
                    video.file_path, video.file_size, video.progress,
                    video.error_message,
                    video.created_at.isoformat(), video.updated_at.isoformat()
                ))
                return True
            except sqlite3.IntegrityError:
                return False

    def update_video(self, video: Video) -> bool:
        """Update an existing video"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE videos SET
                    title = ?, show = ?, url = ?, thumbnail_url = ?,
                    season = ?, episode = ?, year = ?, duration = ?,
                    duration_str = ?, hls_url = ?, status = ?, file_path = ?,
                    file_size = ?, progress = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (
                video.title, video.show, video.url, video.thumbnail_url,
                video.season, video.episode, video.year, video.duration,
                video.duration_str, video.hls_url, video.status.value,
                video.file_path, video.file_size, video.progress,
                video.error_message, datetime.now().isoformat(), video.id
            ))
            return cursor.rowcount > 0

    def get_video(self, video_id: str) -> Optional[Video]:
        """Get a video by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_video(row)
            return None

    def get_all_videos(self) -> List[Video]:
        """Get all videos"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM videos ORDER BY title")
            return [self._row_to_video(row) for row in cursor.fetchall()]

    def search_videos(
        self,
        query: str = "",
        show: Optional[str] = None,
        year: Optional[int] = None,
        status: Optional[VideoStatus] = None
    ) -> List[Video]:
        """Search videos with filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if query:
                conditions.append("(title LIKE ? OR show LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if show:
                conditions.append("show = ?")
                params.append(show)

            if year:
                conditions.append("year = ?")
                params.append(year)

            if status:
                conditions.append("status = ?")
                params.append(status.value)

            sql = "SELECT * FROM videos"
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            sql += " ORDER BY title"

            cursor.execute(sql, params)
            return [self._row_to_video(row) for row in cursor.fetchall()]

    def get_unique_shows(self) -> List[str]:
        """Get list of unique show names"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT show FROM videos ORDER BY show")
            return [row[0] for row in cursor.fetchall()]

    def get_unique_years(self) -> List[int]:
        """Get list of unique years"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT year FROM videos WHERE year IS NOT NULL ORDER BY year DESC")
            return [row[0] for row in cursor.fetchall()]

    def get_video_count(self) -> int:
        """Get total video count"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM videos")
            return cursor.fetchone()[0]

    def update_video_status(self, video_id: str, status: VideoStatus, progress: float = 0, error: str = None):
        """Update video download status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE videos SET status = ?, progress = ?, error_message = ?, updated_at = ?
                WHERE id = ?
            """, (status.value, progress, error, datetime.now().isoformat(), video_id))

    def _row_to_video(self, row: sqlite3.Row) -> Video:
        """Convert database row to Video object"""
        return Video(
            id=row["id"],
            title=row["title"],
            show=row["show"],
            url=row["url"],
            thumbnail_url=row["thumbnail_url"] or "",
            season=row["season"],
            episode=row["episode"],
            year=row["year"],
            duration=row["duration"] or 0,
            duration_str=row["duration_str"] or "",
            hls_url=row["hls_url"],
            status=VideoStatus(row["status"]) if row["status"] else VideoStatus.PENDING,
            file_path=row["file_path"],
            file_size=row["file_size"] or 0,
            progress=row["progress"] or 0,
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
        )

    # Config operations
    def get_config(self, key: str, default: str = "") -> str:
        """Get config value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else default

    def set_config(self, key: str, value: str):
        """Set config value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)
            """, (key, value))

    # Import from JSON
    def import_from_json(self, json_path: Path) -> int:
        """Import videos from JSON file"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        videos = data.get("videos", [])
        imported = 0

        for v in videos:
            # Generate ID from URL
            video_id = v.get("url", "").replace("https://www.pokergo.com/videos/", "").replace("/", "_")
            if not video_id:
                continue

            # Parse show from URL or source
            show = self._extract_show(v)
            year = self._extract_year(v)

            video = Video(
                id=video_id,
                title=v.get("title", "Unknown"),
                show=show,
                url=v.get("url", ""),
                thumbnail_url=v.get("thumbnail", ""),
                year=year,
                duration_str=v.get("duration", ""),
            )

            if self.insert_video(video):
                imported += 1

        return imported

    def _extract_show(self, video_data: dict) -> str:
        """Extract show name from video data"""
        url = video_data.get("url", "").lower()
        title = video_data.get("title", "").lower()
        source = video_data.get("source", "").lower()

        if "wsop" in url or "wsop" in title:
            return "WSOP"
        elif "wpt" in url or "wpt" in title:
            return "WPT"
        elif "high-stakes-poker" in url or "high stakes poker" in title:
            return "High Stakes Poker"
        elif "poker-after-dark" in url or "poker after dark" in title:
            return "Poker After Dark"
        elif "hustler" in url or "hustler" in title:
            return "Hustler Casino Live"
        elif "super-high-roller" in url or "super high roller" in title:
            return "Super High Roller Bowl"
        elif "pgt" in url or "pgt" in title:
            return "PGT"
        else:
            return source.replace("/", "").title() if source else "Other"

    def _extract_year(self, video_data: dict) -> Optional[int]:
        """Extract year from video data"""
        import re

        # 직접 year 필드가 있으면 사용
        if video_data.get("year"):
            try:
                return int(video_data["year"])
            except (ValueError, TypeError):
                pass

        url = video_data.get("url", "")
        title = video_data.get("title", "")

        # Try to find year in URL or title
        for text in [url, title]:
            match = re.search(r"20(1[1-9]|2[0-5])", text)
            if match:
                return int("20" + match.group(1))

        return None

    def export_to_json(self, json_path: Path, filters: dict = None) -> int:
        """Export videos to JSON file"""
        videos = self.get_all_videos() if not filters else self.search_videos(**filters)

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total": len(videos),
            "videos": []
        }

        for v in videos:
            export_data["videos"].append({
                "id": v.id,
                "title": v.title,
                "show": v.show,
                "url": v.url,
                "thumbnail_url": v.thumbnail_url,
                "year": v.year,
                "season": v.season,
                "episode": v.episode,
                "duration_str": v.duration_str,
                "hls_url": v.hls_url,
                "status": v.status.value,
                "file_size": v.file_size,
            })

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        return len(videos)

    def clear_all_videos(self):
        """Clear all videos from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM videos")
            return cursor.rowcount

    def import_wsop_data(self, json_path: Path) -> int:
        """Import WSOP data from scraped JSON"""
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        videos = data.get("videos", [])
        imported = 0

        for v in videos:
            url = v.get("url", "")
            if not url:
                continue

            video_id = url.replace("https://www.pokergo.com/videos/", "").replace("/", "_")

            # 타이틀 처리
            title = v.get("title", "")
            if not title:
                title = video_id.replace("-", " ").replace("_", " ").title()

            video = Video(
                id=video_id,
                title=title,
                show=v.get("source", "WSOP") if "wsop" in url.lower() else self._extract_show(v),
                url=url,
                thumbnail_url=v.get("thumbnail", ""),
                year=self._extract_year(v),
                hls_url=v.get("manifest_url", ""),
            )

            if self.insert_video(video):
                imported += 1

        return imported
