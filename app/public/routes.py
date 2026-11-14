from flask import render_template


def register(app):
    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/features")
    def features():
        return render_template("features.html")

    @app.get("/about")
    def about():
        return render_template("about.html")
