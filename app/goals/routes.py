from datetime import date
from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Goal
from ..services.presenters import goal_row


def register(app):
    @app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        if request.method == "POST":
            deadline = request.form.get("deadline") or None
            try:
                target = Decimal(request.form.get("target_amount", ""))
                saved = Decimal(request.form.get("saved_amount", "0"))
                parsed_deadline = date.fromisoformat(deadline) if deadline else None
            except (InvalidOperation, ValueError):
                flash("Enter valid goal values.")
                return redirect(url_for("goals"))
            name = request.form.get("name", "").strip()
            if not name or target <= 0 or saved < 0:
                flash("Goal name and target amount are required.")
                return redirect(url_for("goals"))
            db.session.add(
                Goal(
                    user_id=session["user_id"],
                    name=name,
                    target_amount=target,
                    saved_amount=saved,
                    deadline=parsed_deadline,
                )
            )
            db.session.commit()
            flash("Goal saved.")
            return redirect(url_for("goals"))
        rows = [
            goal_row(goal)
            for goal in Goal.query.filter_by(user_id=session["user_id"])
            .order_by(Goal.id.desc())
            .all()
        ]
        return render_template("goals.html", goals=rows)
