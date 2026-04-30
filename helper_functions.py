import os
import re
import json
import shutil
import subprocess
import threading
import sys
from urllib.parse import urlparse, parse_qs
import feedparser
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOADS_DIR")
YOUTUBE_DIR = os.getenv("YOUTUBE_DIR")
CACHE_DIR = "cache"

"""
! NOTE FOR DEVELOPER :-
The main function for the project to work are :-
? save_jobs()
? move_to_media()
? run_download()

and feature functions are :-
? clean_rss_feed-()
? youtube_url_to_id()
? youtube_to_rss()
? check_for_videos()
"""

jobs = []
if os.path.exists("data/jobs.json"):
    with open("data/jobs.json", "r") as f:
        jobs = json.load(f)
jobs_lock = threading.Lock()


def save_jobs():
    with jobs_lock:
        with open("data/jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)


def move_to_media():
    download = Path(DOWNLOAD_DIR)
    youtube = Path(YOUTUBE_DIR)

    for src in download.iterdir():
        dst = youtube / src.name

        if src.is_dir() and dst.exists():
            # merge directories
            for item in src.iterdir():
                target = dst / item.name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(item), str(target))
            src.rmdir()
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))


download_lock = threading.Lock()


def run_download(
    url,
    output_dir,
    audio_only,
    audio_format,
    filename_template,
    embed_metadata,
    embed_thumbnail,
    add_metadata,
    move_after,
    extra_args,
    job_index,
):
    jobs[-1]["status"] = "downloading"
    save_jobs()

    cmd = [sys.executable, "-m", "yt_dlp"]

    if audio_only:
        cmd.append("-x")

    if audio_format:
        cmd += ["--audio-format", audio_format]

    if embed_metadata:
        cmd.append("--embed-metadata")

    if embed_thumbnail:
        cmd.append("--embed-thumbnail")

    if add_metadata:
        cmd.append("--add-metadata")

    cmd += ["-o", f"{output_dir}/{filename_template}"]

    if extra_args:
        cmd += extra_args

    cmd.append(url)

    try:
        with download_lock:
            subprocess.run(cmd, check=True)

            if move_after:
                move_to_media()

        jobs[-1]["status"] = "finished"
        save_jobs()

    except Exception as e:
        jobs[-1]["status"] = "error"
        jobs[-1]["error"] = str(e)
        save_jobs()


def clean_rss_feed(link: str):
    feed = feedparser.parse(link)

    videos = []

    for entry in feed.entries:
        videos.append(
            {
                "title": entry.title,
                "url": entry.link,
                "published": entry.published,
                "id": entry.id,
            }
        )

    return videos


def youtube_url_to_id(url):
    parsed = urlparse(url)
    video_id = parse_qs(parsed.query).get("v", [None])[0]
    if not video_id:
        return None
    return f"yt:video:{video_id}"


def youtube_to_rss(url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers, timeout=10).text

    match = re.search(r'"externalId":"(UC[\w-]+)"', html)

    if not match:
        match = re.search(r'"channelId":"(UC[\w-]+)"', html)

    if not match:
        return None

    channel_id = match.group(1)
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def check_for_videos():
    global jobs

    with open("data/settings.json") as f:
        settings = json.load(f)

    while True:
        with open("data/channels.json") as f1:
            channels = json.load(f1)

        with open("data/jobs.json") as f2:
            jobs = json.load(f2)

        existing_ids = {job["id"] for job in jobs}

        for channel in channels:
            videos = clean_rss_feed(channel["rss_url"])
            if not videos:
                continue

            latest = videos[0]

            if latest["id"] not in existing_ids:
                job = {
                    "status": "started",
                    "url": latest["url"],
                    "id": latest["id"],
                }

                jobs.append(job)
                save_jobs()

                thread = threading.Thread(
                    target=run_download,
                    name=latest["id"],
                    args=(
                        latest["url"],
                        channel["prefrences"]["output_dir"],
                        channel["prefrences"]["audio_only"],
                        channel["prefrences"]["audio_format"],
                        channel["prefrences"]["filename_template"],
                        channel["prefrences"]["embed_metadata"],
                        channel["prefrences"]["embed_thumbnail"],
                        channel["prefrences"]["add_metadata"],
                        channel["prefrences"]["move_after"],
                        channel["prefrences"]["extra_args"],
                        latest["id"],
                    ),
                )

                thread.start()

        time.sleep(int(settings["channel_scan_interval"]))


def scan_once():
    global jobs

    with open("data/channels.json") as f1:
            channels = json.load(f1)

    with open("data/jobs.json") as f2:
            jobs = json.load(f2)

    existing_ids = {job["id"] for job in jobs}

    for channel in channels:
        videos = clean_rss_feed(channel["rss_url"])
        if not videos:
                continue

        latest = videos[0]

        if latest["id"] not in existing_ids:
            job = {
                    "status": "started",
                    "url": latest["url"],
                    "id": latest["id"],
                }

            jobs.append(job)
            save_jobs()

            thread = threading.Thread(
                        target=run_download,
                        name=latest["id"],
                        args=(
                            latest["url"],
                            channel["prefrences"]["output_dir"],
                            channel["prefrences"]["audio_only"],
                            channel["prefrences"]["audio_format"],
                            channel["prefrences"]["filename_template"],
                            channel["prefrences"]["embed_metadata"],
                            channel["prefrences"]["embed_thumbnail"],
                            channel["prefrences"]["add_metadata"],
                            channel["prefrences"]["move_after"],
                            channel["prefrences"]["extra_args"],
                            latest["id"],
                        ),
                    )

            thread.start()

THUMB_DIR = f"{CACHE_DIR}/thumb"


VIDEO_EXTENSIONS = (".mkv", ".mp4", ".webm", ".mov", ".avi", ".mp3", ".m4a")


def build_cache():
    for root, dirs, files in os.walk(YOUTUBE_DIR):
        for file in files:
            if not file.lower().endswith(VIDEO_EXTENSIONS):
                continue

            video_path = os.path.join(root, file)

            # preserve folder structure
            rel_path = os.path.relpath(video_path, YOUTUBE_DIR)
            thumb_rel = os.path.splitext(rel_path)[0] + ".jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_rel)

            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

            if os.path.exists(thumb_path):
                continue

            print("Generating:", thumb_rel)

            subprocess.run(
                [
                    "ffmpeg",
                    "-ss",
                    "3",
                    "-i",
                    video_path,
                    "-frames:v",
                    "1",
                    "-vf",
                    "scale=320:-1",
                    "-y",
                    thumb_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )


def generate_thumbnail_cache():
    with open("data/settings.json") as f:
        settings = json.load(f)
    while True:
        build_cache()
        time.sleep(int(settings["generate_thumbnail_cache_interval"]))


if __name__ == "__main__":
    build_cache()
