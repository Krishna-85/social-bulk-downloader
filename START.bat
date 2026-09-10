@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================================
echo              SOCIAL BULK DOWNLOADER
echo                 DEVELOPER: KRISHNA
echo ============================================================
python social_downloader.py
pause
