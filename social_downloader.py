from pathlib import Path
import shutil
import subprocess
import sys

BASE = Path(__file__).resolve().parent
ARCHIVE = BASE / "downloaded_archive.txt"
FAILED = BASE / "failed.txt"

# Prefer the normal Android shared Downloads folder when Termux storage is available.
SHARED_DOWNLOADS = Path.home() / "storage" / "downloads" / "SocialBulkDownloader"
LOCAL_DOWNLOADS = BASE / "Downloads"
DOWNLOADS = SHARED_DOWNLOADS if (Path.home() / "storage" / "downloads").exists() else LOCAL_DOWNLOADS


def banner():
    print(r"""
============================================================
                 SOCIAL BULK DOWNLOADER
                    DEVELOPER: KRISHNA
============================================================
          Facebook  |  Instagram  |  YouTube
============================================================
""")


def site(url: str) -> str:
    u = url.lower()
    if "youtube.com" in u or "youtu.be" in u:
        return "YouTube"
    if "facebook.com" in u or "fb.watch" in u:
        return "Facebook"
    if "instagram.com" in u:
        return "Instagram"
    return "Supported site"


def download(url: str) -> int:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "yt_dlp",
        "--ignore-errors",
        "--no-abort-on-error",
        "--continue",
        "--no-overwrites",
        "--download-archive",
        str(ARCHIVE),
        "--retries",
        "10",
        "--fragment-retries",
        "10",
        "-o",
        str(DOWNLOADS / "%(extractor)s/%(upload_date)s_%(id)s_%(title).150s.%(ext)s"),
        url,
    ]
    return subprocess.run(cmd, cwd=str(BASE)).returncode


def read_urls_from_txt(path: str):
    p = Path(path).expanduser()
    if not p.exists():
        print("File not found:", p)
        return []
    return [
        line.strip()
        for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def main():
    banner()

    print("1. Direct video / Reel URL")
    print("2. YouTube video / playlist / channel URL")
    print("3. TXT file with many URLs")
    print()

    choice = input("Choose [1/2/3]: ").strip()

    if choice == "3":
        path = input("TXT file path: ").strip()
        urls = read_urls_from_txt(path)
        if not urls:
            return
    else:
        url = input("Paste URL: ").strip()
        if not url:
            return
        urls = [url]

    print(f"\n{len(urls)} URL(s) queued.\n")
    print("Download folder:", DOWNLOADS)

    for i, url in enumerate(urls, 1):
        print("=" * 60)
        print(f"[{i}/{len(urls)}] {site(url)}")
        print(url)
        print("=" * 60)
        rc = download(url)
        if rc:
            with FAILED.open("a", encoding="utf-8") as f:
                f.write(url + "\n")

    print("\n" + "=" * 60)
    print("Finished.")
    print("Downloads:", DOWNLOADS)
    print("Archive:", ARCHIVE)
    print("=" * 60)


if __name__ == "__main__":
    main()
