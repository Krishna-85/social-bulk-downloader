#!/data/data/com.termux/files/usr/bin/bash
set -e
printf '\n'
printf '%s\n' '============================================================'
printf '%s\n' '                 SOCIAL BULK DOWNLOADER'
printf '%s\n' '                    DEVELOPER: KRISHNA'
printf '%s\n' '============================================================'
printf '\n'

echo '[1/5] Updating Termux packages...'
pkg update -y

echo '[2/5] Installing Python, FFmpeg, Git, X11 repo...'
pkg install -y python ffmpeg git x11-repo

echo '[3/5] Installing Chromium + Node.js + Termux Playwright runtime...'
# termux-playwright provides the Android-compatible browser automation layer.
pkg install -y chromium nodejs python-greenlet termux-api || true
python -m pip install --no-cache-dir -U yt-dlp termux-playwright
if command -v termux-playwright-install >/dev/null 2>&1; then
  termux-playwright-install || true
fi

echo '[4/5] Setting up shared storage...'
if command -v termux-setup-storage >/dev/null 2>&1; then
  termux-setup-storage || true
fi

echo '[5/5] Setting developer banner...'
BASHRC="$HOME/.bashrc"
MARKER="# --- Social Bulk Downloader / Krishna ---"
if [ -f "$BASHRC" ] && ! grep -Fq "$MARKER" "$BASHRC"; then
cat >> "$BASHRC" <<'BANNER'

# --- Social Bulk Downloader / Krishna ---
printf '\n\033[1;36m============================================================\033[0m\n'
printf '\033[1;33m                 SOCIAL BULK DOWNLOADER\033[0m\n'
printf '\033[1;32m                    DEVELOPER: KRISHNA\033[0m\n'
printf '\033[1;36m============================================================\033[0m\n'
# --- End Social Bulk Downloader / Krishna ---
BANNER
fi
printf '\n%s\n' '============================================================'
printf '%s\n' 'INSTALLATION COMPLETED'
printf '%s\n' '============================================================'
printf '%s\n' 'Run: python social_downloader.py'
printf '%s\n' 'For Facebook/Instagram page Reels, choose option 4.'
printf '%s\n' '============================================================'
printf '\n'
