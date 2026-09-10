# Social Bulk Downloader — Termux

**Developer: Krishna**

A simple Termux wrapper around yt-dlp for downloading authorized content from supported platforms.

## Install

```bash
pkg update -y
pkg install -y git

git clone https://github.com/USERNAME/social-bulk-downloader.git
cd social-bulk-downloader
bash install.sh
```

The installer intentionally **does not upgrade pip itself**. Termux manages its `python-pip` package, and upgrading pip can break that package.

The installer installs:
- Python
- FFmpeg
- Git
- yt-dlp

It also requests shared-storage access when `termux-setup-storage` is available.

## Run

```bash
python social_downloader.py
```

## Menu

1. Direct video / Reel URL
2. YouTube video / playlist / channel URL
3. TXT file with many URLs

## Downloads

If Termux shared storage is available, files are saved to:

```text
~/storage/downloads/SocialBulkDownloader/
```

Otherwise they are saved inside the project's `Downloads/` folder.

## Duplicate protection

`downloaded_archive.txt` is used by yt-dlp so already-downloaded URLs are not intentionally downloaded again.

## Important

This edition handles direct URLs, TXT batches, and collection URLs that yt-dlp itself supports. It does **not** turn a Facebook/Instagram `/reels/` page into a browser-collected 500–1000-item list inside Termux.

Only download content you are authorized to download and follow the platform's terms.
