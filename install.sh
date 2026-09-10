#!/data/data/com.termux/files/usr/bin/bash
set -e

printf '\n'
printf '%s\n' '============================================================'
printf '%s\n' '                 SOCIAL BULK DOWNLOADER'
printf '%s\n' '                    DEVELOPER: KRISHNA'
printf '%s\n' '============================================================'
printf '%s\n\n' '                 TERMUX INSTALLER V5'

fail() {
  printf '\nERROR: %s\n' "$1" >&2
  printf '%s\n' 'Installation stopped. Fix the error above and run: bash install.sh' >&2
  exit 1
}

echo '[1/6] Updating Termux package lists...'
pkg update -y || fail 'Termux package update failed.'

echo '[2/6] Installing required Termux packages...'
pkg install -y python ffmpeg git x11-repo chromium nodejs python-greenlet termux-api || fail 'A required Termux package could not be installed.'

echo '[3/6] Installing yt-dlp and Android Playwright runtime...'
# IMPORTANT: Do NOT upgrade pip itself. Termux manages python-pip as an OS package.
python -m pip install --no-cache-dir -U yt-dlp termux-playwright || fail 'Python dependency installation failed.'

echo '[4/6] Installing the Playwright core wheel for Termux...'
if command -v termux-playwright-install >/dev/null 2>&1; then
  termux-playwright-install || fail 'termux-playwright-install failed. Chromium/Playwright cannot be initialized.'
else
  fail 'termux-playwright-install command was not found after installing termux-playwright.'
fi

echo '[5/6] Verifying browser automation...'
python - <<'PY' || exit 1
import importlib.util
mods = ['termux_playwright', 'playwright']
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    print('Missing Python modules:', ', '.join(missing))
    raise SystemExit(2)
import termux_playwright
import playwright
print('OK: termux_playwright =', getattr(termux_playwright, '__version__', 'installed'))
print('OK: playwright =', getattr(playwright, '__version__', 'installed'))
PY
[ $? -eq 0 ] || fail 'Playwright verification failed.'

if command -v termux-setup-storage >/dev/null 2>&1; then
  echo '[6/6] Setting up Android shared storage...'
  termux-setup-storage || true
else
  echo '[6/6] termux-setup-storage is unavailable; using Termux home storage.'
fi

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
printf '%s\n' 'INSTALLATION COMPLETED SUCCESSFULLY'
printf '%s\n' '============================================================'
printf '%s\n' 'Run: python social_downloader.py'
printf '%s\n' 'For Facebook/Instagram page Reels, choose option 4.'
printf '%s\n\n' '============================================================'
