import json
import os
import threading
from pathlib import Path

from app import app
from helper_functions import (
    check_for_videos_in_channel,
    generate_thumbnail_cache,
    scan_playlists,
)

if __name__ == "__main__":
    # inital file checks
    if not Path("data/jobs.json").exists():
        with open("data/jobs.json") as file:
            json.dump([], file)
    if not Path("data/channels.json").exists():
        with open("data/channels.json") as file:
            json.dump([], file)
    if not Path("data/playlists.json").exists():
        with open("data/playlists.json") as file:
            json.dump([], file)
    if not Path("data/settings.json").exists():
        with open("data/settings.json") as file:
            json.dump({}, file)

    # inital daemon intialization and debug environment variable extraction
    debug = os.getenv("DEBUG", "false").lower() == "true"
    threading.Thread(
        target=check_for_videos_in_channel, daemon=True, name="Video Scanner"
    ).start()
    threading.Thread(
        target=generate_thumbnail_cache, daemon=True, name="Thumbnail Generator"
    ).start()
    threading.Thread(
        target=scan_playlists, daemon=True, name="Playlist Scanner"
    ).start()
    # App running
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug,
    )
