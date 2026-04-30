from flask import Flask, request, jsonify, render_template, send_from_directory
import threading
import os
import uuid
import json
from urllib.parse import unquote

from helper_functions import *

app = Flask(
    __name__, template_folder="templates", static_folder="static", static_url_path="/"
)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(YOUTUBE_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download")
def download():
    return render_template("download.html")


@app.route("/jobs")
def jobs_():
    return render_template("jobs.html")


@app.route("/channels")
def channels():
    return render_template("chanels.html")


@app.route("/settings")
def settings():
    return render_template("settings.html")


@app.route("/api/download", methods=["POST"])
def api_download():
    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "url required"}), 400

    jobs.append({"status": "queued", "url": url, "id": youtube_url_to_id(url)})
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
            youtube_url_to_id(url),
        ),
    )

    thread.start()
    jobs[-1] = {"status": "started", "url": url, "id": youtube_url_to_id(url)}
    save_jobs()
    return jsonify(
        {
            "job_id": jobs.index(
                {"status": "started", "url": url, "id": youtube_url_to_id(url)}
            ),
            "status": "started",
        }
    )


@app.route("/api/status/<job_id>")
def api_status(job_id):
    job_id = int(job_id)
    job = jobs[job_id]

    if not job:
        return jsonify({"error": "job not found"}), 404

    return jsonify(job)


@app.route("/api/jobs")
def api_all_jobs():
    return jsonify(jobs)


@app.route("/api/feed", methods=["POST"])
def api_feed():
    data = request.get_json()
    url = data.get("url")
    cleaned = clean_rss_feed(youtube_to_rss(url))

    return jsonify(cleaned)


@app.route("/api/subscribe", methods=["POST", "GET", "DELETE"])
def api_subscribe():
    global subscriptions

    # safe load
    try:
        if os.path.exists("data/channels.json"):
            with open("data/channels.json", "r") as f:
                content = f.read().strip()
                subscriptions = json.loads(content) if content else []
        else:
            subscriptions = []
    except Exception:
        subscriptions = []
    if request.method == "GET":
        return jsonify(subscriptions), 200

    elif request.method == "POST":
        data = request.get_json()
        url = data.get("url")
        prefrences = data.get("prefrences")

        if not url:
            return jsonify({"error": "url required"}), 400

        rss_url = youtube_to_rss(url)

        sub = {
            "id": str(uuid.uuid4()),
            "youtube_url": url,
            "rss_url": rss_url,
            "last_seen_id": None,
            "enabled": True,
            "prefrences": prefrences,
        }

        subscriptions.append(sub)

        with open("data/channels.json", "w") as f:
            json.dump(subscriptions, f, indent=2)

        return jsonify(sub), 201

    elif request.method == "DELETE":
        data = request.get_json()
        sub_id = data.get("id")

        new_list = [s for s in subscriptions if s["id"] != sub_id]

        if len(new_list) == len(subscriptions):
            return jsonify({"error": "not found"}), 404

        subscriptions = new_list

        with open("data/channels.json", "w") as f:
            json.dump(subscriptions, f, indent=2)

        return jsonify({"message": "removed"}), 200

    return jsonify({"message": "405 Method Not Allowed"}), 405


@app.route("/api/check_for_videos", methods=["GET"])
def api_check_for_videos():
    new_videos = check_for_videos()
    return jsonify({"code": 200, "New Videos": new_videos}), 200


@app.route("/api/generate_thumbnail_cache", methods=["GET"])
def api_generate_thumbnail_cache():
    build_cache()
    return jsonify({"code": 200, "message": "Cache Built"}), 200


@app.route("/api/thumbs/<path:name>")
def api_thumbs(name):
    name = unquote(name)
    return send_from_directory("cache/thumb", name)


@app.route("/api/videos/<path:name>")
def api_videos(name):
    name = unquote(name)
    return send_from_directory(YOUTUBE_DIR, name)


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    if request.method == "GET":
        if os.path.exists("data/settings.json"):
            with open("data/settings.json", "r") as f:
                content = f.read().strip()
                settings = (
                    json.loads(content)
                    if content
                    else {
                        "channel_scan_interval": 86400,
                        "generate_thumbnail_cache_interval": 86400,
                    }
                )
        else:
            settings = {
                "channel_scan_interval": 86400,
                "generate_thumbnail_cache_interval": 86400,
            }

        return jsonify({"code": 200, "settings": settings}), 200
    if request.method == "POST":
        data = request.json

        settings = {
            "channel_scan_interval": data["channel_scan_interval"],
            "generate_thumbnail_cache_interval": data[
                "generate_thumbnail_cache_interval"
            ],
        }
        with open("data/settings.json", "w") as f:
            json.dump(settings, f, indent=2)

        return jsonify({"code": 201, "message": "Settings Updated Succesfully"}), 201


@app.route("/api/videosDownloaded")
def api_videos_downloaded():
    videos = []

    for root, _, files in os.walk(YOUTUBE_DIR):
        for file in files:
            if file.lower().endswith(".mkv"):

                full_path = os.path.join(root, file)

                rel_path = os.path.relpath(full_path, YOUTUBE_DIR)
                rel_path = rel_path.replace("\\", "/")  # 🔥 FIX 1

                thumb_rel_path = os.path.splitext(rel_path)[0] + ".jpg"
                thumb_rel_path = thumb_rel_path.replace("\\", "/")

                videos.append(
                    {
                        "name": file,
                        "path": rel_path,
                        "thumbnail": thumb_rel_path,
                        "thumbnail_full": os.path.join(
                            "cache/thumb", thumb_rel_path
                        ).replace("\\", "/"),
                    }
                )

    return jsonify(videos)


if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false").lower() == "true"
    threading.Thread(target=check_for_videos, daemon=True).start()
    threading.Thread(target=generate_thumbnail_cache, daemon=True).start()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug,
    )
