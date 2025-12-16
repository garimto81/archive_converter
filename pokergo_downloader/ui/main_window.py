"""Main Window UI"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QCheckBox, QProgressBar, QStatusBar, QMessageBox,
    QSplitter, QFrame, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QIcon

from ..core.database import Database
from ..models.video import Video, VideoStatus
from .download_dialog import DownloadDialog
from .settings_dialog import SettingsDialog


class MainWindow(QMainWindow):
    """Main application window"""

    download_requested = pyqtSignal(list)  # List of video IDs

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.videos = []
        self.selected_ids = set()

        self.init_ui()
        self.load_videos()

    def init_ui(self):
        """Initialize UI components"""
        self.setWindowTitle("PokerGO Downloader v1.0")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)

        # Search and filter
        search_layout = self._create_search_bar()
        layout.addLayout(search_layout)

        # Video table
        self.table = self._create_table()
        layout.addWidget(self.table)

        # Bottom bar (selection info + download button)
        bottom_bar = self._create_bottom_bar()
        layout.addLayout(bottom_bar)

        # Status bar
        self.statusBar().showMessage("Ready")

        # Menu bar
        self._create_menu()

    def _create_toolbar(self) -> QHBoxLayout:
        """Create toolbar with action buttons"""
        layout = QHBoxLayout()

        # Refresh button
        self.btn_refresh = QPushButton("Refresh List")
        self.btn_refresh.clicked.connect(self.refresh_list)
        layout.addWidget(self.btn_refresh)

        # Import button
        self.btn_import = QPushButton("Import JSON")
        self.btn_import.clicked.connect(self.import_json)
        layout.addWidget(self.btn_import)

        # Export button
        self.btn_export = QPushButton("Export JSON")
        self.btn_export.clicked.connect(self.export_json)
        layout.addWidget(self.btn_export)

        # Import WSOP Data button
        self.btn_import_wsop = QPushButton("Import WSOP Data")
        self.btn_import_wsop.clicked.connect(self.import_wsop_data)
        layout.addWidget(self.btn_import_wsop)

        # Settings button
        self.btn_settings = QPushButton("Settings")
        self.btn_settings.clicked.connect(self.show_settings)
        layout.addWidget(self.btn_settings)

        layout.addStretch()

        # Video count label
        self.lbl_count = QLabel("0 videos")
        layout.addWidget(self.lbl_count)

        return layout

    def _create_search_bar(self) -> QHBoxLayout:
        """Create search and filter bar"""
        layout = QHBoxLayout()

        # Search input
        layout.addWidget(QLabel("Search:"))
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Enter keywords...")
        self.txt_search.textChanged.connect(self.filter_videos)
        self.txt_search.setMinimumWidth(200)
        layout.addWidget(self.txt_search)

        # Show filter
        layout.addWidget(QLabel("Show:"))
        self.cmb_show = QComboBox()
        self.cmb_show.addItem("All Shows", None)
        self.cmb_show.currentIndexChanged.connect(self.filter_videos)
        self.cmb_show.setMinimumWidth(150)
        layout.addWidget(self.cmb_show)

        # Year filter
        layout.addWidget(QLabel("Year:"))
        self.cmb_year = QComboBox()
        self.cmb_year.addItem("All Years", None)
        self.cmb_year.currentIndexChanged.connect(self.filter_videos)
        self.cmb_year.setMinimumWidth(100)
        layout.addWidget(self.cmb_year)

        # Status filter
        layout.addWidget(QLabel("Status:"))
        self.cmb_status = QComboBox()
        self.cmb_status.addItem("All", None)
        self.cmb_status.addItem("Pending", VideoStatus.PENDING.value)
        self.cmb_status.addItem("Completed", VideoStatus.COMPLETED.value)
        self.cmb_status.addItem("Failed", VideoStatus.FAILED.value)
        self.cmb_status.currentIndexChanged.connect(self.filter_videos)
        self.cmb_status.setMinimumWidth(100)
        layout.addWidget(self.cmb_status)

        # Clear filters button
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_filters)
        layout.addWidget(self.btn_clear)

        layout.addStretch()

        return layout

    def _create_table(self) -> QTableWidget:
        """Create video table"""
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "", "Title", "Show", "Year", "Duration", "Status", "Size"
        ])

        # Column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)

        table.setColumnWidth(0, 40)   # Checkbox
        table.setColumnWidth(2, 150)  # Show
        table.setColumnWidth(3, 60)   # Year
        table.setColumnWidth(4, 100)  # Duration
        table.setColumnWidth(5, 100)  # Status
        table.setColumnWidth(6, 100)  # Size

        # Selection behavior
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)

        # Header checkbox for select all
        self.header_checkbox = QCheckBox()
        self.header_checkbox.stateChanged.connect(self.toggle_select_all)
        table.setCellWidget(0, 0, self.header_checkbox)

        return table

    def _create_bottom_bar(self) -> QHBoxLayout:
        """Create bottom bar with selection info and download button"""
        layout = QHBoxLayout()

        # Selection info
        self.lbl_selected = QLabel("Selected: 0 videos")
        layout.addWidget(self.lbl_selected)

        self.lbl_estimated_size = QLabel("Est. Size: 0 GB")
        layout.addWidget(self.lbl_estimated_size)

        layout.addStretch()

        # Fetch HLS URLs button
        self.btn_fetch_hls = QPushButton("Fetch HLS URLs")
        self.btn_fetch_hls.setMinimumWidth(130)
        self.btn_fetch_hls.setEnabled(False)
        self.btn_fetch_hls.clicked.connect(self.fetch_hls_urls)
        layout.addWidget(self.btn_fetch_hls)

        # Download button
        self.btn_download = QPushButton("Download Selected")
        self.btn_download.setMinimumWidth(150)
        self.btn_download.setEnabled(False)
        self.btn_download.clicked.connect(self.start_download)
        layout.addWidget(self.btn_download)

        return layout

    def _create_menu(self):
        """Create menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        import_action = QAction("Import JSON...", self)
        import_action.triggered.connect(self.import_json)
        file_menu.addAction(import_action)

        export_action = QAction("Export JSON...", self)
        export_action.triggered.connect(self.export_json)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        import_wsop_action = QAction("Import WSOP Data...", self)
        import_wsop_action.triggered.connect(self.import_wsop_data)
        file_menu.addAction(import_wsop_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu("Tools")

        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def load_videos(self):
        """Load videos from database"""
        self.videos = self.db.get_all_videos()
        self.update_filters()
        self.update_table()
        self.update_count()

    def update_filters(self):
        """Update filter dropdowns"""
        # Save current selections
        current_show = self.cmb_show.currentData()
        current_year = self.cmb_year.currentData()

        # Update shows
        self.cmb_show.clear()
        self.cmb_show.addItem("All Shows", None)
        for show in self.db.get_unique_shows():
            self.cmb_show.addItem(show, show)

        # Restore selection
        if current_show:
            index = self.cmb_show.findData(current_show)
            if index >= 0:
                self.cmb_show.setCurrentIndex(index)

        # Update years
        self.cmb_year.clear()
        self.cmb_year.addItem("All Years", None)
        for year in self.db.get_unique_years():
            self.cmb_year.addItem(str(year), year)

        # Restore selection
        if current_year:
            index = self.cmb_year.findData(current_year)
            if index >= 0:
                self.cmb_year.setCurrentIndex(index)

    def update_table(self):
        """Update table with current videos"""
        self.table.setRowCount(len(self.videos))

        for row, video in enumerate(self.videos):
            # Checkbox
            checkbox = QCheckBox()
            checkbox.setChecked(video.id in self.selected_ids)
            checkbox.stateChanged.connect(lambda state, vid=video.id: self.on_checkbox_changed(vid, state))
            self.table.setCellWidget(row, 0, checkbox)

            # Title
            self.table.setItem(row, 1, QTableWidgetItem(video.title))

            # Show
            self.table.setItem(row, 2, QTableWidgetItem(video.show))

            # Year
            year_str = str(video.year) if video.year else "-"
            self.table.setItem(row, 3, QTableWidgetItem(year_str))

            # Duration
            self.table.setItem(row, 4, QTableWidgetItem(video.duration_str or "-"))

            # Status
            status_item = QTableWidgetItem(video.status.value.title())
            if video.status == VideoStatus.COMPLETED:
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif video.status == VideoStatus.FAILED:
                status_item.setForeground(Qt.GlobalColor.red)
            elif video.status == VideoStatus.DOWNLOADING:
                status_item.setForeground(Qt.GlobalColor.blue)
            self.table.setItem(row, 5, status_item)

            # Size
            size_str = video.file_size_str if video.file_size > 0 else "-"
            self.table.setItem(row, 6, QTableWidgetItem(size_str))

    def update_count(self):
        """Update video count label"""
        total = self.db.get_video_count()
        filtered = len(self.videos)
        if total == filtered:
            self.lbl_count.setText(f"{total} videos")
        else:
            self.lbl_count.setText(f"{filtered} / {total} videos")

    def update_selection_info(self):
        """Update selection info labels"""
        count = len(self.selected_ids)
        self.lbl_selected.setText(f"Selected: {count} videos")

        # Estimate size (assume ~1.5 GB per video)
        est_size = count * 1.5
        self.lbl_estimated_size.setText(f"Est. Size: ~{est_size:.1f} GB")

        self.btn_fetch_hls.setEnabled(count > 0)
        self.btn_download.setEnabled(count > 0)

    def filter_videos(self):
        """Filter videos based on search and filters"""
        query = self.txt_search.text()
        show = self.cmb_show.currentData()
        year = self.cmb_year.currentData()
        status_value = self.cmb_status.currentData()
        status = VideoStatus(status_value) if status_value else None

        self.videos = self.db.search_videos(query, show, year, status)
        self.update_table()
        self.update_count()

    def clear_filters(self):
        """Clear all filters"""
        self.txt_search.clear()
        self.cmb_show.setCurrentIndex(0)
        self.cmb_year.setCurrentIndex(0)
        self.cmb_status.setCurrentIndex(0)

    def on_checkbox_changed(self, video_id: str, state: int):
        """Handle checkbox state change"""
        if state == Qt.CheckState.Checked.value:
            self.selected_ids.add(video_id)
        else:
            self.selected_ids.discard(video_id)
        self.update_selection_info()

    def toggle_select_all(self, state: int):
        """Toggle select all visible videos"""
        checked = state == Qt.CheckState.Checked.value

        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)

    def refresh_list(self):
        """Refresh video list from database"""
        self.load_videos()
        self.statusBar().showMessage("List refreshed", 3000)

    def import_json(self):
        """Import videos from JSON file"""
        from PyQt6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                count = self.db.import_from_json(Path(file_path))
                self.load_videos()
                QMessageBox.information(
                    self, "Import Complete",
                    f"Imported {count} new videos."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error",
                    f"Failed to import: {str(e)}"
                )

    def export_json(self):
        """Export videos to JSON file"""
        from PyQt6.QtWidgets import QFileDialog
        from datetime import datetime

        # Default filename with timestamp
        default_name = f"pokergo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", default_name, "JSON Files (*.json)"
        )

        if file_path:
            try:
                count = self.db.export_to_json(Path(file_path))
                QMessageBox.information(
                    self, "Export Complete",
                    f"Exported {count} videos to:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export: {str(e)}"
                )

    def import_wsop_data(self):
        """Import WSOP data from scraped JSON"""
        from PyQt6.QtWidgets import QFileDialog

        # Default to data/pokergo directory
        default_dir = str(Path(__file__).parent.parent.parent / "data" / "pokergo")

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import WSOP Data", default_dir, "JSON Files (*.json)"
        )

        if file_path:
            try:
                count = self.db.import_wsop_data(Path(file_path))
                self.load_videos()
                QMessageBox.information(
                    self, "Import Complete",
                    f"Imported {count} WSOP videos."
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Import Error",
                    f"Failed to import WSOP data: {str(e)}"
                )

    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.db, self)
        dialog.exec()

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About PokerGO Downloader",
            "PokerGO Video Downloader v1.0\n\n"
            "Download poker videos from PokerGO.\n\n"
            "Built with PyQt6 and yt-dlp."
        )

    def fetch_hls_urls(self):
        """Fetch HLS URLs for selected videos"""
        if not self.selected_ids:
            return

        # Check credentials
        email = self.db.get_config("pokergo_email", "")
        password = self.db.get_config("pokergo_password", "")

        if not email or not password:
            QMessageBox.warning(
                self, "Credentials Required",
                "Please configure PokerGO credentials in Settings first."
            )
            self.show_settings()
            return

        # Get selected videos without HLS URL
        selected_videos = [v for v in self.videos if v.id in self.selected_ids and not v.hls_url]

        if not selected_videos:
            QMessageBox.information(
                self, "No Videos",
                "All selected videos already have HLS URLs."
            )
            return

        # Confirm action
        reply = QMessageBox.question(
            self, "Fetch HLS URLs",
            f"Fetch HLS URLs for {len(selected_videos)} videos?\n\n"
            "This will log into PokerGO and extract download URLs.\n"
            "This may take a few minutes.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Show progress dialog
        from .fetch_dialog import FetchDialog
        dialog = FetchDialog(self.db, selected_videos, email, password, self)
        dialog.exec()

        # Refresh after fetching
        self.load_videos()
        self.statusBar().showMessage(f"HLS URLs fetched", 3000)

    def start_download(self):
        """Start downloading selected videos"""
        if not self.selected_ids:
            return

        # Get selected videos
        selected_videos = [v for v in self.videos if v.id in self.selected_ids]

        # Check if any selected videos have HLS URL
        videos_with_hls = [v for v in selected_videos if v.hls_url]
        videos_without_hls = [v for v in selected_videos if not v.hls_url]

        if videos_without_hls:
            reply = QMessageBox.question(
                self, "Missing HLS URLs",
                f"{len(videos_without_hls)} videos don't have HLS URLs.\n\n"
                "Would you like to fetch HLS URLs first?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.fetch_hls_urls()
                return
            elif reply == QMessageBox.StandardButton.Cancel:
                return
            # Continue with videos that have HLS URLs
            selected_videos = videos_with_hls

        if not selected_videos:
            QMessageBox.warning(
                self, "No Downloadable Videos",
                "No videos with HLS URLs selected."
            )
            return

        # Show download dialog
        dialog = DownloadDialog(self.db, selected_videos, self)
        dialog.exec()

        # Refresh after download
        self.load_videos()
        self.selected_ids.clear()
        self.update_selection_info()
