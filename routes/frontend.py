from flask import Flask, render_template


def frontend(app: Flask):
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
        return render_template("channels.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    @app.route("/playlists")
    def playlists():
        return render_template("playlists.html")

    @app.route("/createPlaylists")
    def create_playlists():
        return render_template("playlist_file.html")

    @app.route("/channelNames")
    def channel_names():
        return render_template("channel_names.html")
