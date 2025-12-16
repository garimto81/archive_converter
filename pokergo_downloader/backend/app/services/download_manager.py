"""Download Manager Service"""

import asyncio
import subprocess
import re
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

from ..config import settings
from ..models.download import DownloadQueueItem, DownloadQueueResponse, DownloadStatus
from .database import get_db


@dataclass
class DownloadTask:
    """Download task"""
    video_id: str
    video_title: str
    url: str
    output_path: Path
    quality: str
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: float = 0.0
    eta: int = 0
    error_message: Optional[str] = None
    process: Optional[subprocess.Popen] = None


class DownloadManager:
    """Manages download queue and workers"""

    def __init__(self):
        self.queue: List[DownloadTask] = []
        self.active: Dict[str, DownloadTask] = {}
        self.completed: List[DownloadTask] = []
        self.is_running = False
        self._lock = asyncio.Lock()
        self._ws_manager = None

    def set_ws_manager(self, manager):
        """Set WebSocket manager for progress updates"""
        self._ws_manager = manager

    def add_to_queue(self, video_ids: List[str], quality: str = "Best") -> int:
        """Add videos to download queue"""
        db = get_db()
        added = 0

        for video_id in video_ids:
            # Check if already in queue or active
            if video_id in self.active:
                continue
            if any(t.video_id == video_id for t in self.queue):
                continue

            video = db.get_video(video_id)
            if not video or not video.hls_url:
                continue

            # Create task
            safe_title = self._sanitize_filename(video.title)
            output_path = Path(db.get_config("download_path", str(settings.download_path)))
            output_path = output_path / f"{safe_title}.mp4"

            task = DownloadTask(
                video_id=video_id,
                video_title=video.title,
                url=video.hls_url,
                output_path=output_path,
                quality=quality,
            )

            self.queue.append(task)
            added += 1

        # Start processing if not running
        if added > 0 and not self.is_running:
            asyncio.create_task(self._process_queue())

        return added

    async def _process_queue(self):
        """Process download queue"""
        self.is_running = True

        while self.queue or self.active:
            # Fill active slots
            while (
                self.queue
                and len(self.active) < settings.max_concurrent_downloads
            ):
                task = self.queue.pop(0)
                self.active[task.video_id] = task
                asyncio.create_task(self._download_video(task))

            await asyncio.sleep(1)

        self.is_running = False

    async def _download_video(self, task: DownloadTask):
        """Download a single video"""
        task.status = DownloadStatus.DOWNLOADING
        db = get_db()

        # Update database status
        from pokergo_downloader.models.video import VideoStatus
        db.update_video_status(task.video_id, VideoStatus.DOWNLOADING)

        # Build yt-dlp command
        format_selector = self._get_format_selector(task.quality)
        cmd = [
            "yt-dlp",
            "-f", format_selector,
            "-o", str(task.output_path),
            "--no-check-certificate",
            "--newline",
            "--progress-template", "%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
            task.url,
        ]

        try:
            task.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )

            async for line in task.process.stdout:
                line = line.decode().strip()
                if "|" in line and "%" in line:
                    try:
                        parts = line.split("|")
                        percent_str = parts[0].replace("%", "").strip()
                        task.progress = float(percent_str) if percent_str != "N/A" else 0

                        speed_str = parts[1].strip() if len(parts) > 1 else "0"
                        task.speed = self._parse_speed(speed_str)

                        eta_str = parts[2].strip() if len(parts) > 2 else "0"
                        task.eta = self._parse_eta(eta_str)

                        # Send WebSocket update
                        if self._ws_manager:
                            await self._ws_manager.send_progress(
                                task.video_id,
                                task.progress,
                                task.speed,
                                task.eta,
                                task.status.value,
                            )
                    except Exception:
                        pass

            await task.process.wait()

            if task.process.returncode == 0:
                task.status = DownloadStatus.COMPLETED
                task.progress = 100

                # Get file size
                file_size = task.output_path.stat().st_size if task.output_path.exists() else 0

                # Update database
                db.update_video_status(task.video_id, VideoStatus.COMPLETED, 100)

                # Send WebSocket notification
                if self._ws_manager:
                    await self._ws_manager.send_completed(
                        task.video_id,
                        str(task.output_path),
                        file_size,
                    )
            else:
                task.status = DownloadStatus.FAILED
                task.error_message = f"yt-dlp error (code: {task.process.returncode})"
                db.update_video_status(task.video_id, VideoStatus.FAILED, 0, task.error_message)

                if self._ws_manager:
                    await self._ws_manager.send_failed(task.video_id, task.error_message)

        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error_message = str(e)
            db.update_video_status(task.video_id, VideoStatus.FAILED, 0, task.error_message)

            if self._ws_manager:
                await self._ws_manager.send_failed(task.video_id, task.error_message)

        finally:
            # Move from active to completed
            if task.video_id in self.active:
                del self.active[task.video_id]
            self.completed.append(task)

    def _get_format_selector(self, quality: str) -> str:
        """Get yt-dlp format selector"""
        quality_map = {
            "Best": "best",
            "1080p": "1080p/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p": "720p/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "480p": "480p/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        }
        return quality_map.get(quality, "best")

    def _sanitize_filename(self, title: str) -> str:
        """Sanitize filename"""
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        filename = title
        for char in invalid_chars:
            filename = filename.replace(char, '-')
        while '  ' in filename:
            filename = filename.replace('  ', ' ')
        while '--' in filename:
            filename = filename.replace('--', '-')
        return filename.strip(' -')[:150]

    def _parse_speed(self, speed_str: str) -> float:
        """Parse speed string to bytes/s"""
        if not speed_str or speed_str == "N/A":
            return 0
        try:
            match = re.search(r"([\d.]+)\s*(Ki?B|Mi?B|Gi?B)?/s", speed_str, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                unit = match.group(2) or "B"
                unit = unit.upper()
                if "G" in unit:
                    return value * 1024 * 1024 * 1024
                elif "M" in unit:
                    return value * 1024 * 1024
                elif "K" in unit:
                    return value * 1024
                return value
        except (ValueError, IndexError):
            pass
        return 0

    def _parse_eta(self, eta_str: str) -> int:
        """Parse ETA string to seconds"""
        if not eta_str or eta_str == "N/A":
            return 0
        try:
            parts = eta_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0

    def get_queue_status(self) -> DownloadQueueResponse:
        """Get current queue status"""
        active_items = [
            DownloadQueueItem(
                id=i,
                video_id=t.video_id,
                video_title=t.video_title,
                status=t.status,
                progress=t.progress,
                speed=t.speed,
                eta=t.eta,
            )
            for i, t in enumerate(self.active.values())
        ]

        queued_items = [
            DownloadQueueItem(
                id=i,
                video_id=t.video_id,
                video_title=t.video_title,
                status=t.status,
            )
            for i, t in enumerate(self.queue)
        ]

        completed_items = [
            DownloadQueueItem(
                id=i,
                video_id=t.video_id,
                video_title=t.video_title,
                status=t.status,
                progress=t.progress,
                error_message=t.error_message,
            )
            for i, t in enumerate(self.completed[-10:])  # Last 10
        ]

        return DownloadQueueResponse(
            active=active_items,
            queued=queued_items,
            completed=completed_items,
            total_active=len(self.active),
            total_queued=len(self.queue),
        )

    def cancel_download(self, video_id: str) -> bool:
        """Cancel a download"""
        if video_id in self.active:
            task = self.active[video_id]
            if task.process:
                task.process.terminate()
            task.status = DownloadStatus.CANCELLED
            return True

        for i, task in enumerate(self.queue):
            if task.video_id == video_id:
                self.queue.pop(i)
                return True

        return False

    def pause_download(self, video_id: str) -> bool:
        """Pause a download"""
        if video_id in self.active:
            task = self.active[video_id]
            if task.process:
                task.process.terminate()
            task.status = DownloadStatus.PAUSED
            # Move to front of queue
            del self.active[video_id]
            self.queue.insert(0, task)
            return True
        return False

    def resume_download(self, video_id: str) -> bool:
        """Resume a paused download"""
        for task in self.queue:
            if task.video_id == video_id and task.status == DownloadStatus.PAUSED:
                task.status = DownloadStatus.QUEUED
                return True
        return False

    def pause_all(self):
        """Pause all downloads"""
        for video_id in list(self.active.keys()):
            self.pause_download(video_id)

    def resume_all(self):
        """Resume all paused downloads"""
        for task in self.queue:
            if task.status == DownloadStatus.PAUSED:
                task.status = DownloadStatus.QUEUED

    def clear_completed(self) -> int:
        """Clear completed downloads"""
        count = len(self.completed)
        self.completed.clear()
        return count


# Singleton instance
_manager_instance: Optional[DownloadManager] = None


def get_download_manager() -> DownloadManager:
    """Get download manager instance"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DownloadManager()
    return _manager_instance
