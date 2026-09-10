# Termux setup

## Install

```bash
git clone https://github.com/Krishna-85/social-bulk-downloader.git
cd social-bulk-downloader
bash install.sh
```

The installer installs Python, FFmpeg, Git, Chromium and the Android-compatible `termux-playwright` runtime. It intentionally does **not** upgrade Termux's `pip` package.

## Facebook / Instagram Reels page

```bash
python social_downloader.py
```

Select:

```text
4. Facebook / Instagram page → auto-collect Reels → download
```

Paste a page such as:

```text
https://www.facebook.com/official.anuragthakur/reels/
```

Then enter the number of Reels to collect, for example `500`.

The collector scrolls the rendered page, saves discovered Reel URLs to `collected_urls.txt`, then opens each Reel in Chromium and looks for its rendered video media. It does not send the `/reels/` listing URL to yt-dlp as if it were a playlist.

### Authentication

Public pages may work without login. If Facebook presents a login wall, the page needs to be accessible in an authorized session. Do not put your Facebook password in this project or in GitHub.

### Android reliability

For long jobs, keep Termux battery usage unrestricted and avoid force-closing Termux. A WakeLock is requested when supported.

## Output

Downloads:

```text
Internal Storage/Download/SocialBulkDownloader/
```

Project records:

- `downloaded_archive.txt` — completed yt-dlp downloads
- `failed.txt` — URLs that failed
- `collected_urls.txt` — Reel URLs collected by the browser
