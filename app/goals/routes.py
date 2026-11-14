from datetime import date
from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Goal, GoalContribution, Transaction
from ..services.presenters import goal_row


def _goal_values(form):
    deadline = form.get("deadline") or None
    try:
        target = Decimal(form.get("target_amount", ""))
        saved = Decimal(form.get("saved_amount", "0"))
        parsed_deadline = date.fromisoformat(deadline) if deadline else None
    except (InvalidOperation, ValueError):
        raise ValueError("Enter valid goal values.") from None
    name = form.get("name", "").strip()
    if not name or target <= 0 or saved < 0:
        raise ValueError("Goal name and target amount are required.")
    return {
        "name": name,
        "target_amount": target,
        "saved_amount": saved,
        "deadline": parsed_deadline,
    }


def register(app):
    @app.route("/goals", methods=["GET", "POST"])
    @login_required
    def goals():
        if request.method == "POST":
            try:
                values = _goal_values(request.form)
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("goals"))
            db.session.add(Goal(user_id=session["user_id"], **values))
            db.session.commit()
            flash("Goal saved.")
            return redirect(url_for("goals"))
        query = Goal.query.filter_by(user_id=session["user_id"])
        if request.args.get("show_archived") != "1":
            query = query.filter_by(archived=False)
        rows = [goal_row(goal) for goal in query.order_by(Goal.id.desc()).all()]
        return render_template("goals.html", goals=rows, showing_archived=request.args.get("show_archived") == "1")

    @app.route("/goals/<int:goal_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_goal(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        if request.method == "POST":
            try:
                values = _goal_values(request.form)
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("edit_goal", goal_id=goal.id))
            for key, value in values.items():
                setattr(goal, key, value)
            db.session.commit()
            flash("Goal updated.")
            return redirect(url_for("goals"))
        return render_template("goal_edit.html", goal=goal)

    @app.post("/goals/<int:goal_id>/contributions")
    @login_required
    def add_goal_contribution(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        try:
            amount = Decimal(request.form.get("amount", ""))
            contribution_date = date.fromisoformat(request.form.get("date", ""))
        except (InvalidOperation, ValueError):
            flash("Enter a valid contribution amount and date.")
            return redirect(url_for("goals"))
        if amount <= 0:
            flash("Contribution must be greater than zero.")
            return redirect(url_for("goals"))
        transaction_id = request.form.get("transaction_id") or None
        if transaction_id:
            transaction = Transaction.query.filter_by(
                id=transaction_id, user_id=session["user_id"]
            ).first()
            if transaction is None:
                flash("That transaction does not belong to your account.")
                return redirect(url_for("goals"))
        db.session.add(
            GoalContribution(
                user_id=session["user_id"],
                goal=goal,
                transaction_id=transaction_id,
                amount=amount,
                date=contribution_date,
                note=request.form.get("note", "").strip() or None,
            )
        )
        db.session.commit()
        flash("Goal contribution added.")
        return redirect(url_for("goals"))

    @app.post("/goals/<int:goal_id>/archive")
    @login_required
    def archive_goal(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        goal.archived = not goal.archived
        db.session.commit()
        flash("Goal archive status updated.")
        return redirect(url_for("goals", show_archived="1" if goal.archived else None))

    @app.post("/goals/<int:goal_id>/delete")
    @login_required
    def delete_goal(goal_id):
        goal = Goal.query.filter_by(id=goal_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(goal)
        db.session.commit()
        flash("Goal deleted.")
        return redirect(url_for("goals"))
