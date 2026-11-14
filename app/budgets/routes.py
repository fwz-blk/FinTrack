from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Budget, Category, Transaction
from ..services.budgets import spent_for_budget
from ..services.presenters import budget_row


def _budget_values(form):
    try:
        amount = Decimal(form.get("amount", ""))
        warning_threshold = int(form.get("warning_threshold", "80"))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter valid budget values.") from None
    name = form.get("name", "").strip()
    category = form.get("category", "All").strip() or "All"
    period = form.get("period", "monthly")
    rollover = form.get("rollover") == "on"
    if not name or amount <= 0:
        raise ValueError("Budget name and amount are required.")
    if period not in {"weekly", "monthly", "yearly"}:
        raise ValueError("Choose a valid budget period.")
    if not 1 <= warning_threshold <= 100:
        raise ValueError("Warning threshold must be between 1 and 100.")
    return {
        "name": name,
        "amount": amount,
        "category": category,
        "period": period,
        "warning_threshold": warning_threshold,
        "rollover": rollover,
    }


def register(app):
    @app.route("/budgets", methods=["GET", "POST"])
    @login_required
    def budgets():
        if request.method == "POST":
            try:
                values = _budget_values(request.form)
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("budgets"))
            db.session.add(Budget(user_id=session["user_id"], spent=Decimal("0.00"), **values))
            db.session.commit()
            flash("Budget saved.")
            return redirect(url_for("budgets"))
        user_id = session["user_id"]
        rows = []
        for budget in Budget.query.filter_by(user_id=user_id).order_by(Budget.id.desc()).all():
            spent, limit = spent_for_budget(budget, user_id)
            rows.append(budget_row(budget, spent, limit))
        categories = sorted(
            {category.name for category in Category.query.filter_by(user_id=user_id)}
            | {transaction.category for transaction in Transaction.query.filter_by(user_id=user_id)}
        )
        return render_template("budgets.html", budgets=rows, categories=categories)

    @app.route("/budgets/<int:budget_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_budget(budget_id):
        budget = Budget.query.filter_by(id=budget_id, user_id=session["user_id"]).first_or_404()
        if request.method == "POST":
            try:
                values = _budget_values(request.form)
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("edit_budget", budget_id=budget.id))
            for key, value in values.items():
                setattr(budget, key, value)
            db.session.commit()
            flash("Budget updated.")
            return redirect(url_for("budgets"))
        user_id = session["user_id"]
        categories = sorted(
            {category.name for category in Category.query.filter_by(user_id=user_id)}
            | {transaction.category for transaction in Transaction.query.filter_by(user_id=user_id)}
        )
        return render_template("budget_edit.html", budget=budget, categories=categories)

    @app.post("/budgets/<int:budget_id>/delete")
    @login_required
    def delete_budget(budget_id):
        budget = Budget.query.filter_by(id=budget_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(budget)
        db.session.commit()
        flash("Budget deleted.")
        return redirect(url_for("budgets"))
