import os
import threading

from app import app
from helper_functions import check_for_videos_in_channel, generate_thumbnail_cache

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "false").lower() == "true"
    threading.Thread(
        target=check_for_videos_in_channel, daemon=True, name="Video Scanner"
    ).start()
    threading.Thread(
        target=generate_thumbnail_cache, daemon=True, name="Thumbnail Generator"
    ).start()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=debug,
    )
