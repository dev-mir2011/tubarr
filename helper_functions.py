import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import feedparser
import requests
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

"""
! Metadata handeling functions :-
save_jobs()
move_to_media()
clean_rss_feed()
youtube_video_url_to_id()
youtube_channel_url_to_rss_url()
youtube_playlist_url_to_rss_url()
check_for_videos()
scan_once()
build_cache()
generate_thumbnail_cache()
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


def youtube_video_url_to_id(url):
    parsed = urlparse(url)
    video_id = parse_qs(parsed.query).get("v", [None])[0]
    if not video_id:
        return None
    return f"yt:video:{video_id}"


def youtube_channel_url_to_rss_url(url: str) -> str | None:
    headers = {"User-Agent": "Mozilla/5.0"}
    html = requests.get(url, headers=headers, timeout=10).text

    match = re.search(r'"externalId":"(UC[\w-]+)"', html)

    if not match:
        match = re.search(r'"channelId":"(UC[\w-]+)"', html)

    if not match:
        return None

    channel_id = match.group(1)
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def youtube_playlist_url_to_rss_url(url: str) -> str | None:
    parsed = urlparse(url)

    if "youtube.com" in parsed.netloc:
        query = parse_qs(parsed.query)

        if "list" in query:
            playlist_id = query["list"][0]
            return f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"

    if "youtu.be" in parsed.netloc:
        query = parse_qs(parsed.query)

        if "list" in query:
            playlist_id = query["list"][0]
            return f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"

    return None


def check_for_videos_in_channel():
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


def scan_channels_once():
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

VIDEO_EXTENSIONS = (".mkv", ".mp4", ".webm", ".mov", ".avi")
AUDIO_EXTENSIONS = (".mp3", ".m4a", ".flac", ".wav", ".ogg")


def make_placeholder(thumb_path: str):
    subprocess.run(
        [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "color=c=gray:s=320x180",
            "-frames:v",
            "1",
            "-y",
            thumb_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def build_cache():
    for root, _, files in os.walk(YOUTUBE_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()

            if ext not in VIDEO_EXTENSIONS + AUDIO_EXTENSIONS:
                continue

            media_path = os.path.join(root, file)

            rel_path = os.path.relpath(media_path, YOUTUBE_DIR)
            thumb_rel = os.path.splitext(rel_path)[0] + ".jpg"
            thumb_path = os.path.join(THUMB_DIR, thumb_rel)

            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)

            if os.path.exists(thumb_path):
                continue

            print("Generating:", thumb_rel)

            if ext in VIDEO_EXTENSIONS:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-ss",
                        "3",
                        "-i",
                        media_path,
                        "-frames:v",
                        "1",
                        "-vf",
                        "scale=320:-1",
                        "-y",
                        thumb_path,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )

                if result.returncode != 0:
                    print("Video thumb failed:", file)
                    make_placeholder(thumb_path)

            else:
                result = subprocess.run(
                    [
                        "ffmpeg",
                        "-i",
                        media_path,
                        "-an",
                        "-vcodec",
                        "copy",
                        "-map",
                        "0:v:0",
                        "-y",
                        thumb_path,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )

                if result.returncode != 0:
                    make_placeholder(thumb_path)


def generate_thumbnail_cache():
    with open("data/settings.json") as f:
        settings = json.load(f)
    while True:
        build_cache()
        time.sleep(int(settings["generate_thumbnail_cache_interval"]))


# ? Playlist scanning and monitoring and downloading


def get_playlist_data(url: str):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "yt_dlp",
            "--flat-playlist",
            "--dump-single-json",
            url,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    data = json.loads(result.stdout)

    final_data = data["entries"]

    return final_data


def playlist_data_cleanup(entries: list):
    new_data = []
    for entry in entries:
        new_data.append({"id": f"yt:video:{entry['id']}", "url": entry["url"]})

    return new_data


def scan_playlists_once():
    global jobs

    with open("data/playlists.json") as f1:
        playlists = json.load(f1)

    with open("data/jobs.json") as f2:
        jobs = json.load(f2)

    existing_ids = {job["id"] for job in jobs}

    for playlist in playlists:
        videos = playlist_data_cleanup(
            get_playlist_data(playlist["youtube_playlist_url"])
        )
        if not videos:
            continue

        latest = videos[-1]

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
                    playlist["prefrences"]["output_dir"],
                    playlist["prefrences"]["audio_only"],
                    playlist["prefrences"]["audio_format"],
                    playlist["prefrences"]["filename_template"],
                    playlist["prefrences"]["embed_metadata"],
                    playlist["prefrences"]["embed_thumbnail"],
                    playlist["prefrences"]["add_metadata"],
                    playlist["prefrences"]["move_after"],
                    playlist["prefrences"]["extra_args"],
                    latest["id"],
                ),
            )

            thread.start()


def scan_playlists():
    with open("data/settings.json") as f:
        settings = json.load(f)
    while True:
        scan_playlists_once()
        time.sleep(int(settings["scan_playlists_interval"]))


VIDEO_EXTENSIONS = (".mkv", ".mp4", ".webm", ".mov", ".avi", ".mp3", ".m4a")


def create_m3u(folder, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for root, _, files in os.walk(folder):
            for file in sorted(files):
                if file.lower().endswith(VIDEO_EXTENSIONS):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, folder)
                    rel_path = rel_path.replace("\\", "/")

                    f.write(f"{rel_path}\n")


if __name__ == "__main__":
    create_m3u("youtube\Kawaii RomCom Mangas", "Kawaii RomCom Mangas.m3")
