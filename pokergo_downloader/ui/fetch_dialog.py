"""HLS URL Fetch Dialog"""

import asyncio
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal

from ..core.database import Database
from ..core.scraper import PokerGOScraper
from ..models.video import Video


class FetchWorker(QThread):
    """Background worker for fetching HLS URLs"""

    progress_updated = pyqtSignal(int, int, str)  # current, total, video_title
    video_completed = pyqtSignal(str, str, bool)  # video_id, hls_url, success
    log_message = pyqtSignal(str)
    login_status = pyqtSignal(bool)

    def __init__(self, videos: List[Video], email: str, password: str):
        super().__init__()
        self.videos = videos
        self.email = email
        self.password = password
        self.is_running = True

    def run(self):
        """Run fetch process"""
        asyncio.run(self._async_run())

    async def _async_run(self):
        """Async fetch process"""
        scraper = PokerGOScraper(self.email, self.password)

        try:
            self.log_message.emit("Starting browser...")
            await scraper.start(headless=True)

            self.log_message.emit("Logging into PokerGO...")
            if not await scraper.login():
                self.log_message.emit("Login failed! Check credentials.")
                self.login_status.emit(False)
                return

            self.log_message.emit("Login successful!")
            self.login_status.emit(True)

            total = len(self.videos)
            for i, video in enumerate(self.videos):
                if not self.is_running:
                    break

                self.progress_updated.emit(i + 1, total, video.title[:50])
                self.log_message.emit(f"Fetching: {video.title[:40]}...")

                hls_url = await scraper.get_hls_url(video.url)

                if hls_url:
                    self.video_completed.emit(video.id, hls_url, True)
                    self.log_message.emit("  -> Found HLS URL")
                else:
                    self.video_completed.emit(video.id, "", False)
                    self.log_message.emit("  -> No HLS URL found")

                # Small delay
                await asyncio.sleep(0.5)

        except Exception as e:
            self.log_message.emit(f"Error: {str(e)}")
        finally:
            await scraper.close()
            self.log_message.emit("Browser closed.")

    def stop(self):
        """Stop fetch process"""
        self.is_running = False


class FetchDialog(QDialog):
    """HLS URL fetch progress dialog"""

    def __init__(self, db: Database, videos: List[Video], email: str, password: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.videos = videos
        self.email = email
        self.password = password
        self.worker: Optional[FetchWorker] = None
        self.success_count = 0
        self.total_count = len(videos)

        self.init_ui()
        self.start_fetch()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Fetching HLS URLs")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Progress
        self.lbl_status = QLabel("Initializing...")
        layout.addWidget(self.lbl_status)

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        layout.addWidget(self.progress)

        self.lbl_count = QLabel(f"0 / {self.total_count}")
        layout.addWidget(self.lbl_count)

        # Log
        layout.addWidget(QLabel("Log:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        # Buttons
        btn_layout = QHBoxLayout()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_fetch)
        btn_layout.addWidget(self.btn_cancel)

        btn_layout.addStretch()

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setEnabled(False)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def start_fetch(self):
        """Start fetch worker"""
        self.worker = FetchWorker(self.videos, self.email, self.password)
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.video_completed.connect(self.on_video_completed)
        self.worker.log_message.connect(self.on_log_message)
        self.worker.login_status.connect(self.on_login_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress_updated(self, current: int, total: int, title: str):
        """Handle progress update"""
        percent = int((current / total) * 100)
        self.progress.setValue(percent)
        self.lbl_status.setText(f"Processing: {title}")
        self.lbl_count.setText(f"{current} / {total}")

    def on_video_completed(self, video_id: str, hls_url: str, success: bool):
        """Handle video completion"""
        if success and hls_url:
            self.success_count += 1
            # Update database
            video = self.db.get_video(video_id)
            if video:
                video.hls_url = hls_url
                self.db.update_video(video)

    def on_log_message(self, message: str):
        """Handle log message"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def on_login_status(self, success: bool):
        """Handle login status"""
        if not success:
            self.btn_cancel.setEnabled(False)
            self.btn_close.setEnabled(True)
            self.lbl_status.setText("Login Failed")

    def on_finished(self):
        """Handle fetch finished"""
        self.btn_cancel.setEnabled(False)
        self.btn_close.setEnabled(True)

        self.lbl_status.setText("Completed!")
        self.log_text.append("=" * 40)
        self.log_text.append(f"Success: {self.success_count} / {self.total_count}")

        if self.success_count > 0:
            QMessageBox.information(
                self, "Fetch Complete",
                f"Successfully fetched {self.success_count} HLS URLs."
            )

    def cancel_fetch(self):
        """Cancel fetch"""
        if self.worker:
            self.worker.stop()
            self.log_text.append("Cancelling...")

    def closeEvent(self, event):
        """Handle close event"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        event.accept()
