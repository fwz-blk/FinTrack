from datetime import timedelta

from flask import current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import User
from .security import make_token, password_error, read_token


def register(app):
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()
            if user is None or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.")
                return render_template("login.html"), 401
            session["user_id"] = user.id
            session["user_name"] = user.name
            session.permanent = True
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            if not name or not email or not password:
                flash("Please complete all required fields.")
                return render_template("register.html"), 400
            if password != confirm_password:
                flash("Passwords do not match.")
                return render_template("register.html"), 400
            if password_message := password_error(password):
                flash(password_message)
                return render_template("register.html"), 400
            if User.query.filter_by(email=email).first() is not None:
                flash("An account with that email already exists.")
                return render_template("register.html"), 409
            user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
            )
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            session["user_name"] = user.name
            session.permanent = True
            if current_app.config.get("ENV") == "development":
                verification_token = make_token("email-verification", user)
                flash(
                    f"Development verification link: "
                    f"{url_for('verify_email', token=verification_token, _external=True)}"
                )
            return redirect(url_for("dashboard"))
        return render_template("register.html")

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("landing"))

    @app.route("/forgot-password", methods=["GET", "POST"])
    def forgot_password():
        token = None
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user:
                token = make_token("password-reset", user)
                if current_app.config.get("ENV") == "development":
                    flash(f"Development reset link: {url_for('reset_password', token=token, _external=True)}")
            flash("If an account exists for that email, reset instructions are available.")
        return render_template("forgot_password.html")

    @app.route("/reset-password/<token>", methods=["GET", "POST"])
    def reset_password(token):
        payload = read_token("password-reset", token)
        user = db.session.get(User, payload["user_id"]) if payload else None
        if not user or payload["version"] != user.reset_token_version:
            flash("That password reset link is invalid or expired.")
            return redirect(url_for("forgot_password"))
        if request.method == "POST":
            password = request.form.get("password", "")
            if message := password_error(password):
                flash(message)
                return render_template("reset_password.html")
            if password != request.form.get("confirm_password", ""):
                flash("Passwords do not match.")
                return render_template("reset_password.html")
            user.password_hash = generate_password_hash(password)
            user.reset_token_version += 1
            db.session.commit()
            flash("Your password has been updated. Please log in.")
            return redirect(url_for("login"))
        return render_template("reset_password.html")

    @app.get("/verify-email/<token>")
    def verify_email(token):
        payload = read_token("email-verification", token, max_age=timedelta(days=2).total_seconds())
        user = db.session.get(User, payload["user_id"]) if payload else None
        if not user:
            flash("That verification link is invalid or expired.")
        else:
            user.email_verified = True
            db.session.commit()
            flash("Your email address has been verified.")
        return redirect(url_for("login"))
