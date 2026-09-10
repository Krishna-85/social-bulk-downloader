from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent
DOWNLOADS=BASE/"Downloads"
ARCHIVE=BASE/"downloaded_archive.txt"
FAILED=BASE/"failed.txt"

def site(url):
    u=url.lower()
    if "youtube.com" in u or "youtu.be" in u: return "YouTube"
    if "facebook.com" in u or "fb.watch" in u: return "Facebook"
    if "instagram.com" in u: return "Instagram"
    return "Supported site"

def download(url):
    DOWNLOADS.mkdir(exist_ok=True)
    cmd=[
        sys.executable,"-m","yt_dlp",
        "--ignore-errors","--no-abort-on-error",
        "--continue","--no-overwrites",
        "--download-archive",str(ARCHIVE),
        "--retries","10","--fragment-retries","10",
        "-o",str(DOWNLOADS/"%(extractor)s/%(upload_date)s_%(id)s_%(title).150s.%(ext)s"),
        url
    ]
    return subprocess.run(cmd,cwd=str(BASE)).returncode

def main():
    print("="*55)
    print("        SOCIAL BULK DOWNLOADER - TERMUX")
    print("        Facebook • Instagram • YouTube")
    print("="*55)
    print()
    print("1. Direct video / Reel URL")
    print("2. YouTube video / playlist / channel URL")
    print("3. TXT file with many URLs")
    print()

    choice=input("Choose [1/2/3]: ").strip()

    if choice=="3":
        path=input("TXT file path: ").strip()
        p=Path(path).expanduser()
        if not p.exists():
            print("File not found:",p); return
        urls=[x.strip() for x in p.read_text(encoding="utf-8").splitlines()
              if x.strip() and not x.lstrip().startswith("#")]
    else:
        url=input("Paste URL: ").strip()
        if not url: return
        urls=[url]

    print(f"\n{len(urls)} URL(s) queued.\n")

    for i,url in enumerate(urls,1):
        print("="*55)
        print(f"[{i}/{len(urls)}] {site(url)}")
        print(url)
        print("="*55)
        rc=download(url)
        if rc:
            with FAILED.open("a",encoding="utf-8") as f:
                f.write(url+"\n")

    print("\n==============================================")
    print("Finished.")
    print("Downloads:",DOWNLOADS)
    print("==============================================")

if __name__=="__main__":
    main()
