@echo off
echo ================================================
echo PokerGO Downloader - Build Script (Windows)
echo ================================================

cd /d "%~dp0"

echo.
echo [1/4] Installing dependencies...
pip install -r requirements.txt

echo.
echo [2/4] Installing PyInstaller...
pip install pyinstaller>=6.3.0

echo.
echo [3/4] Building executable...
pyinstaller pokergo_downloader.spec --clean --noconfirm

echo.
echo [4/4] Creating data directory...
if not exist "dist\PokerGO_Downloader\data\pokergo" mkdir "dist\PokerGO_Downloader\data\pokergo"

echo.
echo ================================================
echo Build complete!
echo ================================================
echo Output: dist\PokerGO_Downloader\
echo Run: dist\PokerGO_Downloader\PokerGO_Downloader.exe
echo ================================================

pause
