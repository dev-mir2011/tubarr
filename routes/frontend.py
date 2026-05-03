from flask import render_template


def frontend(app):
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
