import json
from datetime import datetime, timezone

from flask import Response, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..auth.decorators import login_required
from ..auth.security import password_error
from ..extensions import db
from ..models import User


def _account_export(user):
    return {
        "profile": {
            "name": user.name,
            "email": user.email,
            "currency": user.currency,
            "timezone": user.timezone,
            "preferences": user.preferences or {},
        },
        "transactions": [
            {
                "date": item.date.isoformat(),
                "type": item.transaction_type,
                "amount": str(item.amount),
                "category": item.category,
                "account": item.account,
                "note": item.note,
            }
            for item in user.transactions
        ],
        "budgets": [
            {"name": item.name, "amount": str(item.amount), "category": item.category, "period": item.period}
            for item in user.budgets
        ],
        "goals": [
            {"name": item.name, "target_amount": str(item.target_amount), "saved_amount": str(item.saved_amount)}
            for item in user.goals
        ],
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }


def register(app):
    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    def settings():
        user = db.get_or_404(User, session["user_id"])
        if request.method == "POST":
            action = request.form.get("action", "profile")
            if action == "profile":
                name = request.form.get("name", "").strip()
                email = request.form.get("email", "").strip().lower()
                if not name or not email:
                    flash("Name and email are required.")
                    return redirect(url_for("settings", tab="profile"))
                if User.query.filter(User.email == email, User.id != user.id).first():
                    flash("That email is already in use.")
                    return redirect(url_for("settings", tab="profile"))
                user.name = name
                user.email = email
                user.currency = request.form.get("currency", "USD").upper()[:3]
                user.timezone = request.form.get("timezone", "UTC")[:64]
                user.avatar_url = request.form.get("avatar_url", "").strip() or None
                session["user_name"] = name
                flash("Profile saved.")
            elif action == "password":
                current = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                if not check_password_hash(user.password_hash, current):
                    flash("Current password is incorrect.")
                elif message := password_error(new_password):
                    flash(message)
                elif new_password != request.form.get("confirm_password", ""):
                    flash("Passwords do not match.")
                else:
                    user.password_hash = generate_password_hash(new_password)
                    user.reset_token_version += 1
                    flash("Password changed.")
            elif action == "preferences":
                user.preferences = {
                    "notifications": request.form.get("notifications") == "on",
                    "budget_alerts": request.form.get("budget_alerts") == "on",
                }
                flash("Preferences saved.")
            elif action == "anonymize":
                if request.form.get("confirmation") != "ANONYMIZE":
                    flash("Type ANONYMIZE to remove your financial data.")
                else:
                    user.name = "Deleted User"
                    user.email = f"deleted-{user.id}@example.invalid"
                    user.avatar_url = None
                    user.preferences = {}
                    user.transactions.clear()
                    user.budgets.clear()
                    user.goals.clear()
                    user.categories.clear()
                    user.accounts.clear()
                    db.session.commit()
                    session.clear()
                    flash("Your financial data was removed and your account was anonymized.")
                    return redirect(url_for("landing"))
            elif action == "delete":
                if request.form.get("confirmation") != "DELETE":
                    flash("Type DELETE to permanently delete your account.")
                else:
                    db.session.delete(user)
                    db.session.commit()
                    session.clear()
                    return redirect(url_for("landing"))
            db.session.commit()
            return redirect(url_for("settings", tab=action if action in {"profile", "password", "preferences"} else "profile"))
        return render_template(
            "settings.html",
            user=user,
            active_tab=request.args.get("tab", "profile"),
            preferences=user.preferences or {},
        )

    @app.get("/settings/export")
    @login_required
    def settings_export():
        user = db.get_or_404(User, session["user_id"])
        return Response(
            json.dumps(_account_export(user), indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": "attachment; filename=fintrack-account.json"},
        )
