from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import User


def register(app):
    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        user = db.get_or_404(User, session["user_id"])
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            currency = request.form.get("currency", "USD").strip().upper()
            timezone = request.form.get("timezone", "UTC").strip()
            avatar_url = request.form.get("avatar_url", "").strip() or None
            if not name or not email:
                flash("Name and email are required.")
                return redirect(url_for("settings"))
            if User.query.filter(User.email == email, User.id != user.id).first():
                flash("That email is already in use.")
                return redirect(url_for("settings"))
            user.name = name
            user.email = email
            user.currency = currency[:3]
            user.timezone = timezone[:64]
            user.avatar_url = avatar_url
            db.session.commit()
            session["user_name"] = name
            flash("Settings saved.")
            return redirect(url_for("settings"))
        return render_template("settings.html", user=user)
