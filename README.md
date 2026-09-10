# Social Bulk Downloader

**Developer: Krishna**

Termux downloader for authorized/public media URLs using yt-dlp, plus a browser-based collector for Facebook/Instagram Reels pages.

## Features

- YouTube videos, playlists and channels through yt-dlp
- Direct supported video/Reel URLs through yt-dlp
- TXT batch downloads
- **Facebook/Instagram page → auto-scroll → collect Reel URLs → open each Reel in Android Chromium → try to download the rendered media**
- Resume/duplicate protection with `downloaded_archive.txt`
- Downloads to `Internal Storage/Download/SocialBulkDownloader/` when Termux storage is available

## Important

The Facebook/Instagram page collector uses a real browser because a page such as `/official.anuragthakur/reels/` is a listing page, not a single video URL. yt-dlp does not reliably treat that page as a playlist, and Facebook's current Reel extractor can also fail on individual public Reel URLs.

This tool does not bypass private-access controls. If a page requires authentication, use an account/session you are authorized to use.

## Termux

```bash
git clone https://github.com/Krishna-85/social-bulk-downloader.git
cd social-bulk-downloader
bash install.sh
python social_downloader.py
```

Choose **4** for a Facebook/Instagram Reels page.

