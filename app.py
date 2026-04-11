from flask import Flask, request, jsonify
import subprocess
import threading
import os
import shutil
import uuid

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
PHONK_DIR = "phonk"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(PHONK_DIR, exist_ok=True)

jobs = {}


def move_to_phonk():
    for file in os.listdir(DOWNLOAD_DIR):
        src = os.path.join(DOWNLOAD_DIR, file)
        dst = os.path.join(PHONK_DIR, file)

        if os.path.isfile(src):
            shutil.move(src, dst)


def run_download(job_id, url):
    jobs[job_id]["status"] = "downloading"

    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "mp3",
        "-o",
        f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        url,
    ]

    try:
        subprocess.run(cmd, check=True)
        move_to_phonk()
        jobs[job_id]["status"] = "finished"
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)


@app.route("/download", methods=["POST"])
def download():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "url required"}), 400

    job_id = str(uuid.uuid4())

    jobs[job_id] = {
        "status": "queued",
        "url": url
    }

    thread = threading.Thread(target=run_download, args=(job_id, url))
    thread.start()

    return jsonify({
        "job_id": job_id,
        "status": "started"
    })


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
        "phonk_dir": PHONK_DIR
    }


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)