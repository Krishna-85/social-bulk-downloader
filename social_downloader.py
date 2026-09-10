from pathlib import Path
import asyncio
import json
import re
import shutil
import subprocess
import sys
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen

BASE = Path(__file__).resolve().parent
ARCHIVE = BASE / "downloaded_archive.txt"
FAILED = BASE / "failed.txt"
URLS_FILE = BASE / "collected_urls.txt"

SHARED_DOWNLOADS = Path.home() / "storage" / "downloads" / "SocialBulkDownloader"
LOCAL_DOWNLOADS = BASE / "Downloads"
DOWNLOADS = SHARED_DOWNLOADS if (Path.home() / "storage" / "downloads").exists() else LOCAL_DOWNLOADS
BROWSER_PROFILE = BASE / ".browser_profile"


def banner():
    print(r"""
============================================================
                 SOCIAL BULK DOWNLOADER
                    DEVELOPER: KRISHNA
============================================================
      Facebook  |  Instagram  |  YouTube  |  Termux
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


def read_urls_from_txt(path: str):
    p = Path(path).expanduser()
    if not p.exists():
        print("File not found:", p)
        return []
    return [
        line.strip() for line in p.read_text(encoding="utf-8", errors="ignore").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def run_ytdlp(url: str) -> int:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "yt_dlp",
        "--ignore-errors", "--no-abort-on-error", "--continue", "--no-overwrites",
        "--download-archive", str(ARCHIVE),
        "--retries", "10", "--fragment-retries", "10",
        "-o", str(DOWNLOADS / "%(extractor)s/%(upload_date)s_%(id)s_%(title).150s.%(ext)s"),
        url,
    ]
    return subprocess.run(cmd, cwd=str(BASE)).returncode


def looks_like_collection(url: str) -> bool:
    u = url.lower()
    return ("facebook.com" in u and ("/reels" in u or "/people/" in u or "/profile.php" in u)) or (
        "instagram.com" in u and ("/reels" in u or "/reel" in u)
    )


def normalize_reel_url(href: str, base_url: str) -> str | None:
    if not href:
        return None
    if href.startswith("/"):
        parsed = urlparse(base_url)
        href = f"{parsed.scheme}://{parsed.netloc}{href}"
    if not href.startswith("http"):
        return None
    low = href.lower()
    if "facebook.com" in low:
        if re.search(r"facebook\.com/(?:reel|reels/videos)/[A-Za-z0-9._?=&-]+", href, re.I):
            return href.split("&ref=")[0]
        if "facebook.com/watch/" in low and re.search(r"[?&]v=\d+", href):
            return href.split("&ref=")[0]
    if "instagram.com" in low and re.search(r"instagram\.com/reel/[A-Za-z0-9_-]+", href, re.I):
        return href.split("?")[0]
    return None


async def collect_reel_urls(page, page_url: str, target: int, max_scrolls: int = 160):
    found = []
    seen = set()
    no_growth = 0
    last_count = 0

    await page.goto(page_url, timeout=90000, wait_until="domcontentloaded")
    await page.wait_for_timeout(5000)

    for scroll_no in range(1, max_scrolls + 1):
        hrefs = await page.locator("a[href]").evaluate_all("els => els.map(e => e.href).filter(Boolean)")
        for href in hrefs:
            u = normalize_reel_url(href, page_url)
            if u and u not in seen:
                seen.add(u)
                found.append(u)
                if len(found) >= target:
                    break
        print(f"\rScrolling... {scroll_no}/{max_scrolls} | Reel URLs: {len(found)}/{target}", end="", flush=True)
        if len(found) >= target:
            break

        if len(found) == last_count:
            no_growth += 1
        else:
            no_growth = 0
            last_count = len(found)

        if no_growth >= 12:
            # Try a larger jump once the normal scroll stops producing links.
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(3500)
            no_growth = 0
        else:
            await page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 0.85, 700))")
            await page.wait_for_timeout(1800)

    print()
    return found[:target]


def cookie_header(cookies):
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def download_direct_media(media_url: str, cookies, referer: str, output: Path) -> bool:
    """Download a progressive MP4 only; reject images/HTML/HLS playlists."""
    if not media_url.startswith("http"):
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/138 Mobile Safari/537.36",
        "Referer": referer,
        "Accept": "video/mp4,video/*;q=0.9,*/*;q=0.1",
    }
    ch = cookie_header(cookies)
    if ch:
        headers["Cookie"] = ch
    try:
        req = Request(media_url, headers=headers)
        with urlopen(req, timeout=90) as r:
            ctype = (r.headers.get("Content-Type") or "").lower()
            if "mpegurl" in ctype or "m3u8" in ctype or media_url.lower().split("?", 1)[0].endswith(".m3u8"):
                return False
            first = r.read(32)
            # MP4/MOV normally contains an ftyp box near the beginning.
            if b"ftyp" not in first and "video/" not in ctype and not media_url.lower().split("?", 1)[0].endswith(".mp4"):
                print(f"    rejected non-video media: {ctype or 'unknown content type'}")
                return False
            with output.open("wb") as f:
                f.write(first)
                while True:
                    chunk = r.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
        return output.stat().st_size > 10000
    except Exception as e:
        print(f"    direct media download failed: {e}")
        try:
            output.unlink(missing_ok=True)
        except Exception:
            pass
        return False


def download_hls_with_ffmpeg(media_url: str, cookies, referer: str, output: Path) -> bool:
    """Download an HLS stream using ffmpeg, preserving the browser session."""
    if not media_url.startswith("http"):
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    cookie = cookie_header(cookies)
    ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/138 Mobile Safari/537.36"
    header = f"Referer: {referer}\r\nUser-Agent: {ua}\r\n"
    if cookie:
        header += f"Cookie: {cookie}\r\n"
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-headers", header,
        "-i", media_url,
        "-c", "copy",
        str(output),
    ]
    try:
        r = subprocess.run(cmd, cwd=str(BASE), timeout=180, capture_output=True, text=True)
        if r.returncode == 0 and output.exists() and output.stat().st_size > 10000:
            return True
        if r.stderr:
            print("    ffmpeg:", r.stderr.strip()[-500:])
    except Exception as e:
        print(f"    HLS download failed: {e}")
    try:
        output.unlink(missing_ok=True)
    except Exception:
        pass
    return False


def validate_mp4(path: Path) -> bool:
    """Use ffprobe when available to ensure the saved file is a real playable media file."""
    if not path.exists() or path.stat().st_size < 10000:
        return False
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=20,
        )
        return r.returncode == 0 and "video" in r.stdout.lower()
    except Exception:
        # If ffprobe is unavailable, size/type checks in the download functions remain the fallback.
        return True


async def extract_and_download_reel(context, reel_url: str, index: int, total: int):
    page = await context.new_page()
    network_media = []  # list of (url, content-type)

    async def capture_response(response):
        try:
            ctype = (response.headers.get("content-type") or "").lower().split(";", 1)[0].strip()
            u = response.url
            clean = u.lower().split("?", 1)[0]
            if ctype.startswith("video/") or "mpegurl" in ctype or clean.endswith((".mp4", ".m3u8")):
                if not any(item[0] == u for item in network_media):
                    network_media.append((u, ctype))
        except Exception:
            pass

    page.on("response", capture_response)
    try:
        await page.goto(reel_url, timeout=90000, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        media_urls = await page.evaluate("""
        () => {
          const out = [];
          const add = (u) => {
            if (u && typeof u === 'string' && u.startsWith('http') && !out.includes(u)) out.push(u);
          };
          document.querySelectorAll('video').forEach(v => {
            add(v.currentSrc); add(v.src);
            v.querySelectorAll('source').forEach(s => add(s.src));
          });
          document.querySelectorAll('video source').forEach(s => add(s.src));
          return out;
        }
        """)

        # Give late video requests a chance to arrive.
        await page.wait_for_timeout(2500)
        # Add network-captured streams while retaining their response Content-Type.
        for u, ctype in network_media:
            if u not in media_urls:
                media_urls.append(u)

        cookies = await context.cookies()
        title = await page.title()
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:80] or f"reel_{index}"

        # Prefer actual video responses, never generic fbcdn resources such as thumbnails.
        # Build a content-type map from network responses; Facebook often serves
        # signed MP4 URLs that do NOT end in .mp4.
        ctype_map = {u: ctype for u, ctype in network_media}
        candidates = []
        for media_url in media_urls:
            ctype = ctype_map.get(media_url, "")
            low_url = media_url.lower()
            clean = low_url.split("?", 1)[0]
            query = low_url.split("?", 1)[1] if "?" in low_url else ""
            is_hls = clean.endswith(".m3u8") or "mpegurl" in ctype or "m3u8" in query
            is_mp4 = (ctype.startswith("video/") and "mpegurl" not in ctype) or clean.endswith(".mp4") or "mime_type=video%2fmp4" in query or "mime_type=video/mp4" in query
            if is_hls:
                candidates.append((media_url, "hls"))
            elif is_mp4:
                candidates.append((media_url, "mp4"))

        for media_url, kind in candidates:
            out = DOWNLOADS / "Facebook" / f"{index:05d}_{safe_title}.mp4"
            if kind == "hls":
                ok = download_hls_with_ffmpeg(media_url, cookies, reel_url, out)
            else:
                ok = download_direct_media(media_url, cookies, reel_url, out)
            if ok and validate_mp4(out):
                print(f"[{index}/{total}] Downloaded: {out.name}")
                return True
            elif out.exists():
                out.unlink(missing_ok=True)

        print(f"[{index}/{total}] No valid video stream found in browser; trying yt-dlp fallback...")
        rc = run_ytdlp(reel_url)
        return rc == 0
    except Exception as e:
        print(f"[{index}/{total}] Failed: {e}")
        return False
    finally:
        page.remove_listener("response", capture_response)
        await page.close()


async def browser_collect_and_download(page_url: str, target: int):
    try:
        from termux_playwright import async_playwright_termux, launch
    except ImportError:
        print("termux-playwright is not installed.")
        print("Run: python -m pip install -U termux-playwright")
        return

    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    print("\nStarting Android Chromium automation...")
    print("Public pages can be processed without entering your password.")
    print("If Facebook shows a login wall, the page must be accessible in an authorized session.")

    async with async_playwright_termux() as p:
        browser = await launch(
            p,
            headless=True,
            single_process=True,
            low_memory_mode=False,
            jitless=True,
            wake_lock=True,
        )
        try:
            context = await browser.new_context()
            page = await context.new_page()
            urls = await collect_reel_urls(page, page_url, target)
            await page.close()

            if not urls:
                print("\nNo Reel URLs were found. The site may require login or changed its page layout.")
                return

            URLS_FILE.write_text("\n".join(urls) + "\n", encoding="utf-8")
            print(f"\nCollected {len(urls)} Reel URLs.")
            print(f"Saved URL list: {URLS_FILE}")
            print("\nDownloading rendered Reel media (validated MP4 only)...")

            ok = 0
            for i, reel_url in enumerate(urls, 1):
                if await extract_and_download_reel(context, reel_url, i, len(urls)):
                    ok += 1
                else:
                    with FAILED.open("a", encoding="utf-8") as f:
                        f.write(reel_url + "\n")
            await context.close()
            print(f"\nCompleted: {ok}/{len(urls)} downloaded.")
        finally:
            await browser.close()


def main():
    banner()
    print("1. Direct video / Reel URL")
    print("2. YouTube video / playlist / channel URL")
    print("3. TXT file with many URLs")
    print("4. Facebook / Instagram page → auto-collect Reels → download")
    print()
    choice = input("Choose [1/2/3/4]: ").strip()

    if choice == "4":
        page_url = input("Paste Facebook/Instagram Reels page URL: ").strip()
        if not page_url:
            return
        raw = input("How many Reels? [500]: ").strip()
        try:
            target = max(1, min(int(raw or "500"), 2000))
        except ValueError:
            target = 500
        asyncio.run(browser_collect_and_download(page_url, target))
        print("\nDownloads:", DOWNLOADS)
        return

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
        rc = run_ytdlp(url)
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
