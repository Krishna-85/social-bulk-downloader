#!/data/data/com.termux/files/usr/bin/bash
set -e

echo "=============================================="
echo "       SOCIAL BULK DOWNLOADER - TERMUX"
echo "=============================================="

pkg update -y
pkg install -y python ffmpeg git

python -m pip install --upgrade pip
python -m pip install -U yt-dlp

echo
echo "Installation complete."
echo "Run:"
echo "  python social_downloader.py"
echo
