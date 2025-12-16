@echo off
echo Starting PokerGO Downloader...
cd /d "%~dp0"
python -m pokergo_downloader.main
pause
