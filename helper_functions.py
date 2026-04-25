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
    for name in os.listdir(DOWNLOAD_DIR):
        src = os.path.join(DOWNLOAD_DIR, name)
        dst = os.path.join(YOUTUBE_DIR, name)

        if os.path.isdir(src) and os.path.exists(dst):
            # merge directories
            for item in os.listdir(src):
                shutil.move(os.path.join(src, item), os.path.join(dst, item))
            os.rmdir(src)
        else:
            shutil.move(src, dst)


def run_download(
    url,
    output_dir=DOWNLOAD_DIR,
    audio_only=True,
    audio_format="mp3",
    filename_template="%(title)s.%(ext)s",
    embed_metadata=True,
    embed_thumbnail=False,
    add_metadata=True,
    move_after=True,
    extra_args=None,
):
    """
    url,
    output_dir=DOWNLOAD_DIR,
    audio_only=True,
    audio_format="mp3",
    filename_template="%(title)s.%(ext)s",
    embed_metadata=True,
    embed_thumbnail=False,
    add_metadata=True,
    move_after=True,
    extra_args=None,
    """
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

    cmd += [
        "-o",
        f"{output_dir}/{filename_template}",
    ]

    if extra_args:
        cmd += extra_args

    cmd.append(url)

    try:
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

    while True:
        with open("data/channels.json") as f1:
            channels = json.load(f1)

        with open("data/jobs.json") as f2:
            jobs = json.load(f2)

        for channel in channels:
            videos = clean_rss_feed(channel["rss_url"])
            if not videos:
                continue

            latest = videos[0]

            if not jobs or latest["id"] != jobs[-1]["id"]:
                jobs.append(
                    {
                        "status": "queued",
                        "url": latest["url"],
                        "id": latest["id"],
                    }
                )
                save_jobs()

                thread = threading.Thread(
                    target=run_download,
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
                    ),
                )

                thread.start()

                jobs[-1]["status"] = "started"
                save_jobs()
                return True

        time.sleep(86400)
        return False


THUMB_DIR = f"{CACHE_DIR}/thumb"


def build_cache():
    for root, dirs, files in os.walk(YOUTUBE_DIR):
        for file in files:
            if not file.lower().endswith(".mkv"):
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

if __name__ == "__main__":
    build_cache()