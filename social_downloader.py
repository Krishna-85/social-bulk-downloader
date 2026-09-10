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
    if not media_url.startswith("http"):
        return False
    output.parent.mkdir(parents=True, exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/128 Mobile Safari/537.36",
        "Referer": referer,
        "Accept": "*/*",
    }
    ch = cookie_header(cookies)
    if ch:
        headers["Cookie"] = ch
    try:
        req = Request(media_url, headers=headers)
        with urlopen(req, timeout=90) as r, output.open("wb") as f:
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


async def extract_and_download_reel(context, reel_url: str, index: int, total: int):
    page = await context.new_page()
    try:
        await page.goto(reel_url, timeout=90000, wait_until="domcontentloaded")
        await page.wait_for_timeout(3500)

        # Ask the rendered page for the actual media URL instead of giving the
        # Facebook /reels/ listing to yt-dlp. Facebook's extractor currently
        # fails on a number of public Reel URLs, so the browser is the source.
        media_urls = await page.evaluate("""
        () => {
          const out = [];
          const add = (u) => { if (u && typeof u === 'string' && u.startsWith('http') && !out.includes(u)) out.push(u); };
          document.querySelectorAll('video').forEach(v => { add(v.currentSrc); add(v.src); });
          document.querySelectorAll('video source, source').forEach(s => add(s.src));
          for (const e of performance.getEntriesByType('resource')) {
            const u = e.name || '';
            if (/\\.(mp4|m3u8)(\\?|$)/i.test(u) || /fbcdn|video.*facebook|scontent.*fbcdn/i.test(u)) add(u);
          }
          return out.slice(0, 20);
        }
        """)

        cookies = await context.cookies()
        title = await page.title()
        safe_title = re.sub(r"[^A-Za-z0-9._-]+", "_", title).strip("_")[:80] or f"reel_{index}"

        for media_url in media_urls:
            ext = ".mp4" if ".m3u8" not in media_url.lower() else ".mp4"
            out = DOWNLOADS / "Facebook" / f"{index:05d}_{safe_title}{ext}"
            if out.exists() and out.stat().st_size > 10000:
                print(f"[{index}/{total}] Already exists: {out.name}")
                return True
            if download_direct_media(media_url, cookies, reel_url, out):
                print(f"[{index}/{total}] Downloaded: {out.name}")
                return True

        # Last fallback: try yt-dlp on the individual Reel URL. This is not the
        # collection mechanism, and may work when Facebook's extractor is healthy.
        print(f"[{index}/{total}] Browser media URL not found; trying yt-dlp fallback...")
        rc = run_ytdlp(reel_url)
        return rc == 0
    except Exception as e:
        print(f"[{index}/{total}] Failed: {e}")
        return False
    finally:
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
            print("\nDownloading rendered Reel media...")

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
