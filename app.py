# importing initial dependencies
import os

from flask import Flask

from helper_functions import DOWNLOAD_DIR, YOUTUBE_DIR

# importing routes from routes/
from routes.api import api
from routes.frontend import frontend

app = Flask(
    __name__, template_folder="templates", static_folder="static", static_url_path="/"
)

os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(YOUTUBE_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ! Frontend gets served here


frontend(app)

# ? API Routes Start Here
api(app)
