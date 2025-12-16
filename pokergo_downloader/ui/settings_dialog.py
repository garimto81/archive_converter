"""Settings Dialog"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QGroupBox,
    QFormLayout, QSpinBox, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt

from ..core.database import Database


class SettingsDialog(QDialog):
    """Application settings dialog"""

    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Account settings
        account_group = QGroupBox("PokerGO Account")
        account_layout = QFormLayout(account_group)

        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("your@email.com")
        account_layout.addRow("Email:", self.txt_email)

        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("********")
        account_layout.addRow("Password:", self.txt_password)

        layout.addWidget(account_group)

        # Download settings
        download_group = QGroupBox("Download Settings")
        download_layout = QFormLayout(download_group)

        # Download directory
        dir_layout = QHBoxLayout()
        self.txt_download_dir = QLineEdit()
        self.txt_download_dir.setReadOnly(True)
        dir_layout.addWidget(self.txt_download_dir)

        btn_browse = QPushButton("Browse...")
        btn_browse.clicked.connect(self.browse_directory)
        dir_layout.addWidget(btn_browse)

        download_layout.addRow("Download Folder:", dir_layout)

        # Concurrent downloads
        self.spin_concurrent = QSpinBox()
        self.spin_concurrent.setRange(1, 3)
        self.spin_concurrent.setValue(1)
        download_layout.addRow("Concurrent Downloads:", self.spin_concurrent)

        # Video quality
        self.cmb_quality = QComboBox()
        self.cmb_quality.addItems(["Best", "1080p", "720p", "480p"])
        download_layout.addRow("Video Quality:", self.cmb_quality)

        layout.addWidget(download_group)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_save = QPushButton("Save")
        btn_save.clicked.connect(self.save_settings)
        btn_layout.addWidget(btn_save)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def load_settings(self):
        """Load settings from database"""
        self.txt_email.setText(self.db.get_config("pokergo_email", ""))
        self.txt_password.setText(self.db.get_config("pokergo_password", ""))

        download_dir = self.db.get_config("download_dir", "")
        if not download_dir:
            download_dir = str(Path(__file__).parent.parent.parent / "data" / "pokergo" / "downloads")
        self.txt_download_dir.setText(download_dir)

        concurrent = int(self.db.get_config("concurrent_downloads", "1"))
        self.spin_concurrent.setValue(concurrent)

        quality = self.db.get_config("video_quality", "Best")
        index = self.cmb_quality.findText(quality)
        if index >= 0:
            self.cmb_quality.setCurrentIndex(index)

    def save_settings(self):
        """Save settings to database"""
        self.db.set_config("pokergo_email", self.txt_email.text())

        # Only save password if changed (not placeholder)
        if self.txt_password.text() and self.txt_password.text() != "********":
            self.db.set_config("pokergo_password", self.txt_password.text())

        download_dir = self.txt_download_dir.text()
        if download_dir:
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            self.db.set_config("download_dir", download_dir)

        self.db.set_config("concurrent_downloads", str(self.spin_concurrent.value()))
        self.db.set_config("video_quality", self.cmb_quality.currentText())

        QMessageBox.information(self, "Settings", "Settings saved successfully.")
        self.accept()

    def browse_directory(self):
        """Browse for download directory"""
        current = self.txt_download_dir.text()
        directory = QFileDialog.getExistingDirectory(
            self, "Select Download Folder", current
        )

        if directory:
            self.txt_download_dir.setText(directory)
