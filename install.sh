#!/data/data/com.termux/files/usr/bin/bash
set -e

# Social Bulk Downloader - Termux installer
# Developer: Krishna

printf '\n'
printf '%s\n' '============================================================'
printf '%s\n' '                 SOCIAL BULK DOWNLOADER'
printf '%s\n' '                    DEVELOPER: KRISHNA'
printf '%s\n' '============================================================'
printf '\n'

echo '[1/4] Updating Termux packages...'
pkg update -y

echo '[2/4] Installing required packages...'
pkg install -y python ffmpeg git

echo '[3/4] Installing/updating yt-dlp...'
# IMPORTANT: Never upgrade pip itself in Termux. Termux manages python-pip.
# Install yt-dlp using the pip already supplied by Termux.
if command -v yt-dlp >/dev/null 2>&1; then
    python -m pip install -U --no-cache-dir yt-dlp
else
    python -m pip install --no-cache-dir yt-dlp
fi

echo '[4/4] Setting up shared storage (if available)...'
if command -v termux-setup-storage >/dev/null 2>&1; then
    termux-setup-storage || true
fi

# Add a small developer banner to future Termux shell sessions.
BASHRC="$HOME/.bashrc"
MARKER="# --- Social Bulk Downloader / Krishna ---"
if [ -f "$BASHRC" ]; then
    if ! grep -Fq "$MARKER" "$BASHRC"; then
        cat >> "$BASHRC" <<'BANNER'

# --- Social Bulk Downloader / Krishna ---
printf '\n\033[1;36m============================================================\033[0m\n'
printf '\033[1;33m                 SOCIAL BULK DOWNLOADER\033[0m\n'
printf '\033[1;32m                    DEVELOPER: KRISHNA\033[0m\n'
printf '\033[1;36m============================================================\033[0m\n'
# --- End Social Bulk Downloader / Krishna ---
BANNER
    fi
fi

printf '\n'
printf '%s\n' '============================================================'
printf '%s\n' '              INSTALLATION COMPLETED'
printf '%s\n' '============================================================'
printf '%s\n' 'Run the downloader with:'
printf '%s\n' '  python social_downloader.py'
printf '\n'
printf '%s\n' 'Developer: Krishna'
printf '%s\n' '============================================================'
printf '\n'
