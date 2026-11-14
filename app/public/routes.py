from flask import render_template

from ..auth.decorators import login_required


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

    @app.get("/help")
    def help_page():
        return render_template("info.html", page_title="Help", heading="How can we help?", body="Use the dashboard to review your money, Transactions to manage entries, Budgets for limits, and Goals for savings targets. For account help, email support@fintrack.com.")

    @app.get("/terms")
    def terms():
        return render_template("info.html", page_title="Terms of Service", heading="Terms of Service", body="FinTrack is a student project for personal finance tracking. You are responsible for the accuracy of data you enter and should keep your account credentials private.")

    @app.get("/privacy")
    def privacy():
        return render_template("info.html", page_title="Privacy Policy", heading="Privacy Policy", body="FinTrack stores your account and finance records for your use. Records are scoped to your account and are not shown to other users. You can export, anonymize, or delete your data from Settings.")

    @app.get("/bills")
    @login_required
    def bills():
        return render_template("bills.html")
