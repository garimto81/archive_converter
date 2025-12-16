# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PokerGO Downloader
Build with: pyinstaller pokergo_downloader.spec
"""

import sys
import os
from pathlib import Path

# SPECPATH is provided by PyInstaller - points to spec file directory
spec_dir = Path(SPECPATH)
project_root = spec_dir.parent

block_cipher = None

# Collect all Python files
a = Analysis(
    [str(spec_dir / 'main.py')],
    pathex=[str(project_root), str(spec_dir)],
    binaries=[],
    datas=[
        # Include data directory with database and JSON files
        # First try project's data folder, then local data folder
        (str(project_root / 'data' / 'pokergo' / 'pokergo.db'), 'data/pokergo'),
        (str(project_root / 'data' / 'pokergo' / 'wsop_for_app_20251216_155853.json'), 'data/pokergo'),
        (str(project_root / 'data' / 'pokergo' / 'pokergo_merged_all.json'), 'data/pokergo'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        # SQLite
        'sqlite3',
        # App modules
        'pokergo_downloader',
        'pokergo_downloader.core',
        'pokergo_downloader.core.database',
        'pokergo_downloader.core.scraper',
        'pokergo_downloader.models',
        'pokergo_downloader.models.video',
        'pokergo_downloader.ui',
        'pokergo_downloader.ui.main_window',
        'pokergo_downloader.ui.download_dialog',
        'pokergo_downloader.ui.fetch_dialog',
        'pokergo_downloader.ui.settings_dialog',
        # Standard library
        'json',
        'datetime',
        'pathlib',
        're',
        'asyncio',
        'contextlib',
        'typing',
        # Optional - for HLS fetching
        'playwright',
        'playwright.async_api',
        # HTTP
        'httpx',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'unittest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PokerGO_Downloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PokerGO_Downloader_v1.0.1',
)
