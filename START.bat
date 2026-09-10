@echo off
cd /d "%~dp0"
py -m pip install -U yt-dlp
py social_downloader.py
pause
