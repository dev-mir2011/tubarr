from flask import Flask, request, jsonify
import subprocess
import threading
import os
import shutil
import uuid
from dotenv import load_dotenv
import json
import sys

app = Flask(__name__)

load_dotenv()

DOWNLOAD_DIR = os.getenv("DOWNLOADS_DIR")
YOUTUBE_DIR = os.getenv("YOUTUBE_DIR")

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(YOUTUBE_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

jobs = {}
if os.path.exists("data/jobs.json"):
    with open("data/jobs.json", "r") as f:
        jobs.update(json.load(f))
jobs_lock = threading.Lock()


def save_jobs():
    with jobs_lock:
        with open("data/jobs.json", "w") as f:
            json.dump(jobs, f, indent=2)


def move_to_phonk():
    for file in os.listdir(DOWNLOAD_DIR):
        src = os.path.join(DOWNLOAD_DIR, file)
        dst = os.path.join(YOUTUBE_DIR, file)

        if os.path.isfile(src):
            shutil.move(src, dst)


def run_download(
    job_id,
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
    jobs[job_id]["status"] = "downloading"
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
            move_to_phonk()

        jobs[job_id]["status"] = "finished"
        save_jobs()

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        save_jobs()


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "url required"}), 400

    job_id = str(uuid.uuid4())

    jobs[job_id] = {"status": "queued", "url": url}
    save_jobs()

    # optional parameters
    output_dir = data.get("output_dir", DOWNLOAD_DIR)
    audio_only = data.get("audio_only", True)
    audio_format = data.get("audio_format", "mp3")
    filename_template = data.get("filename_template", "%(title)s.%(ext)s")
    embed_metadata = data.get("embed_metadata", True)
    embed_thumbnail = data.get("embed_thumbnail", False)
    add_metadata = data.get("add_metadata", True)
    move_after = data.get("move_after", True)
    extra_args = data.get("extra_args", None)

    thread = threading.Thread(
        target=run_download,
        args=(
            job_id,
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
        ),
    )

    thread.start()
    jobs[job_id] = {"status": "started", "url": url}
    save_jobs()
    return jsonify({"job_id": job_id, "status": "started"})


@app.route("/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)

    if not job:
        return jsonify({"error": "job not found"}), 404

    return jsonify(job)


@app.route("/jobs")
def all_jobs():
    return jsonify(jobs)


@app.route("/")
def index():
    return {
        "status": "running",
        "download_dir": DOWNLOAD_DIR,
        "youtube_dir": YOUTUBE_DIR,
    }


if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false").lower() == "true"
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug,
    )
