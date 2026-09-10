# Social Bulk Downloader — Termux

## Install

```bash
pkg update -y
pkg install -y git
git clone https://github.com/USERNAME/social-bulk-downloader.git
cd social-bulk-downloader
bash install.sh
```

Then:

```bash
python social_downloader.py
```

## Downloads

Files are saved inside:

```text
Downloads/
```

with platform subfolders created by yt-dlp.

## Bulk URLs

Create a text file with one URL per line and choose option `3`.

## Important

This Termux edition is designed for direct URLs, TXT batches, and yt-dlp-supported collection URLs. Desktop browser automation used for dynamically rendered Facebook/Instagram profile pages is not included because Termux does not provide the same desktop Chrome environment.

Use only content you are authorized to download and comply with platform terms.
