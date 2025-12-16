"""Download Progress Dialog"""

import subprocess
import re
from pathlib import Path
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit, QListWidget,
    QListWidgetItem, QFrame, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QColor

from ..core.database import Database
from ..models.video import Video, VideoStatus


class DownloadWorker(QThread):
    """Background download worker thread"""

    progress_updated = pyqtSignal(str, float, float, int)  # video_id, progress, speed, eta
    video_completed = pyqtSignal(str, bool, str)  # video_id, success, message
    log_message = pyqtSignal(str)  # log message

    def __init__(self, videos: List[Video], download_dir: Path, quality: str = "Best"):
        super().__init__()
        self.videos = videos
        self.download_dir = download_dir
        self.quality = quality
        self.is_running = True
        self.is_paused = False
        self.current_process: Optional[subprocess.Popen] = None

    def run(self):
        """Run download process"""
        self.download_dir.mkdir(parents=True, exist_ok=True)

        for video in self.videos:
            if not self.is_running:
                break

            while self.is_paused and self.is_running:
                self.msleep(100)

            if not self.is_running:
                break

            self.log_message.emit(f"Starting: {video.title}")
            success, message = self._download_video(video)
            self.video_completed.emit(video.id, success, message)

            if success:
                self.log_message.emit(f"Completed: {video.title}")
            else:
                self.log_message.emit(f"Failed: {video.title} - {message}")

    def _get_format_selector(self) -> str:
        """Get yt-dlp format selector based on quality setting"""
        # For JWPlayer, try direct format ID first, then fallback to height-based selector
        quality_map = {
            "Best": "best",
            "1080p": "1080p/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
            "720p": "720p/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "480p": "480p/bestvideo[height<=480]+bestaudio/best[height<=480]/best",
        }
        return quality_map.get(self.quality, "best")

    def _sanitize_filename(self, title: str) -> str:
        """Sanitize title for use as filename"""
        # Remove or replace invalid filename characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        filename = title
        for char in invalid_chars:
            filename = filename.replace(char, '-')
        # Remove multiple spaces/dashes
        while '  ' in filename:
            filename = filename.replace('  ', ' ')
        while '--' in filename:
            filename = filename.replace('--', '-')
        # Trim and limit length
        filename = filename.strip(' -')[:150]
        return filename

    def _download_video(self, video: Video) -> tuple[bool, str]:
        """Download a single video"""
        # Use sanitized title as filename
        safe_title = self._sanitize_filename(video.title)
        output_path = self.download_dir / f"{safe_title}.mp4"

        # Skip if already exists
        if output_path.exists():
            return True, "Already exists"

        # Use HLS URL if available, otherwise try video page URL
        url = video.hls_url or video.url

        # Build format selector based on quality setting
        format_selector = self._get_format_selector()

        cmd = [
            "yt-dlp",
            "-f", format_selector,
            "-o", str(output_path),
            "--no-check-certificate",
            "--newline",
            "--progress-template", "%(progress._percent_str)s|%(progress._speed_str)s|%(progress._eta_str)s",
            url
        ]

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in self.current_process.stdout:
                if not self.is_running:
                    self.current_process.terminate()
                    return False, "Cancelled"

                line = line.strip()
                if "|" in line and "%" in line:
                    try:
                        parts = line.split("|")
                        percent_str = parts[0].replace("%", "").strip()
                        progress = float(percent_str) if percent_str != "N/A" else 0

                        speed_str = parts[1].strip() if len(parts) > 1 else "0"
                        speed = self._parse_speed(speed_str)

                        eta_str = parts[2].strip() if len(parts) > 2 else "0"
                        eta = self._parse_eta(eta_str)

                        self.progress_updated.emit(video.id, progress, speed, eta)
                    except (ValueError, IndexError):
                        pass

            self.current_process.wait()

            if self.current_process.returncode == 0:
                # Get file size
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    return True, f"Downloaded ({file_size / (1024**3):.2f} GB)"
                return True, "Downloaded"
            else:
                return False, f"yt-dlp error (code: {self.current_process.returncode})"

        except Exception as e:
            return False, str(e)
        finally:
            self.current_process = None

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
        except (ValueError, AttributeError):
            pass
        return 0

    def _parse_eta(self, eta_str: str) -> int:
        """Parse ETA string to seconds"""
        if not eta_str or eta_str == "N/A":
            return 0

        try:
            # Format: HH:MM:SS or MM:SS
            parts = eta_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
        except (ValueError, IndexError):
            pass
        return 0

    def pause(self):
        """Pause download"""
        self.is_paused = True

    def resume(self):
        """Resume download"""
        self.is_paused = False

    def stop(self):
        """Stop download"""
        self.is_running = False
        if self.current_process:
            self.current_process.terminate()


class DownloadDialog(QDialog):
    """Download progress dialog"""

    def __init__(self, db: Database, videos: List[Video], parent=None):
        super().__init__(parent)
        self.db = db
        self.videos = videos
        self.worker: Optional[DownloadWorker] = None
        self.completed_count = 0
        self.total_count = len(videos)

        self.init_ui()
        self.start_download()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Download Progress")
        self.setMinimumSize(600, 500)
        self.resize(700, 550)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Overall progress
        overall_frame = QFrame()
        overall_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        overall_layout = QVBoxLayout(overall_frame)

        overall_layout.addWidget(QLabel("Overall Progress"))
        self.progress_overall = QProgressBar()
        self.progress_overall.setTextVisible(True)
        overall_layout.addWidget(self.progress_overall)

        self.lbl_overall = QLabel("0 / 0 videos completed")
        overall_layout.addWidget(self.lbl_overall)

        layout.addWidget(overall_frame)

        # Current download
        current_frame = QFrame()
        current_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        current_layout = QVBoxLayout(current_frame)

        current_layout.addWidget(QLabel("Current Download"))
        self.lbl_current = QLabel("Waiting...")
        self.lbl_current.setWordWrap(True)
        current_layout.addWidget(self.lbl_current)

        self.progress_current = QProgressBar()
        self.progress_current.setTextVisible(True)
        current_layout.addWidget(self.progress_current)

        self.lbl_speed = QLabel("Speed: -- | ETA: --")
        current_layout.addWidget(self.lbl_speed)

        layout.addWidget(current_frame)

        # Queue list
        layout.addWidget(QLabel("Queue"))
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(150)
        for video in self.videos:
            item = QListWidgetItem(f"[ ] {video.title}")
            self.queue_list.addItem(item)
        layout.addWidget(self.queue_list)

        # Log
        layout.addWidget(QLabel("Log"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(100)
        layout.addWidget(self.log_text)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_pause = QPushButton("Pause")
        self.btn_pause.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.btn_pause)

        self.btn_cancel = QPushButton("Cancel All")
        self.btn_cancel.clicked.connect(self.cancel_download)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setEnabled(False)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def start_download(self):
        """Start download worker"""
        download_dir = Path(self.db.get_config("download_dir", ""))
        if not download_dir or not download_dir.exists():
            download_dir = Path(__file__).parent.parent.parent / "data" / "pokergo" / "downloads"

        # Get quality setting
        quality = self.db.get_config("video_quality", "Best")

        self.worker = DownloadWorker(self.videos, download_dir, quality)
        self.log_text.append(f"Quality: {quality}")
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.video_completed.connect(self.on_video_completed)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.finished.connect(self.on_download_finished)
        self.worker.start()

        self.log_text.append(f"Starting download of {self.total_count} videos...")

    def on_progress_updated(self, video_id: str, progress: float, speed: float, eta: int):
        """Handle progress update"""
        self.progress_current.setValue(int(progress))

        # Format speed
        if speed >= 1024 * 1024:
            speed_str = f"{speed / (1024**2):.1f} MB/s"
        elif speed >= 1024:
            speed_str = f"{speed / 1024:.0f} KB/s"
        else:
            speed_str = f"{speed:.0f} B/s"

        # Format ETA
        if eta > 0:
            minutes, seconds = divmod(eta, 60)
            eta_str = f"{int(minutes)}:{int(seconds):02d}"
        else:
            eta_str = "--:--"

        self.lbl_speed.setText(f"Speed: {speed_str} | ETA: {eta_str}")

    def on_video_completed(self, video_id: str, success: bool, message: str):
        """Handle video completion"""
        self.completed_count += 1

        # Update overall progress
        percent = int((self.completed_count / self.total_count) * 100)
        self.progress_overall.setValue(percent)
        self.lbl_overall.setText(f"{self.completed_count} / {self.total_count} videos completed")

        # Update queue list
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            if video_id in item.text():
                if success:
                    item.setText(f"[OK] {item.text()[4:]}")
                    item.setForeground(QColor("green"))
                else:
                    item.setText(f"[X] {item.text()[4:]}")
                    item.setForeground(QColor("red"))
                break

        # Update database
        status = VideoStatus.COMPLETED if success else VideoStatus.FAILED
        self.db.update_video_status(video_id, status, 100 if success else 0, None if success else message)

        # Reset current progress
        self.progress_current.setValue(0)
        self.lbl_speed.setText("Speed: -- | ETA: --")

        # Update current label for next video
        remaining = self.total_count - self.completed_count
        if remaining > 0:
            next_video = self.videos[self.completed_count] if self.completed_count < len(self.videos) else None
            if next_video:
                self.lbl_current.setText(next_video.title)

    def on_log_message(self, message: str):
        """Handle log message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def on_download_finished(self):
        """Handle download finished"""
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_close.setEnabled(True)

        self.lbl_current.setText("Download Complete!")
        self.log_text.append("=" * 40)
        self.log_text.append(f"Completed: {self.completed_count} / {self.total_count}")

    def toggle_pause(self):
        """Toggle pause/resume"""
        if self.worker:
            if self.worker.is_paused:
                self.worker.resume()
                self.btn_pause.setText("Pause")
                self.log_text.append("Resumed")
            else:
                self.worker.pause()
                self.btn_pause.setText("Resume")
                self.log_text.append("Paused")

    def cancel_download(self):
        """Cancel download"""
        reply = QMessageBox.question(
            self, "Cancel Download",
            "Are you sure you want to cancel all downloads?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.worker:
                self.worker.stop()
                self.log_text.append("Cancelling...")

    def closeEvent(self, event):
        """Handle close event"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, "Download in Progress",
                "Download is still in progress. Cancel and close?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.worker.stop()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
