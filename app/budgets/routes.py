from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Budget
from ..services.presenters import budget_row


def register(app):
    @app.route("/budgets", methods=["GET", "POST"])
    @login_required
    def budgets():
        if request.method == "POST":
            try:
                amount = Decimal(request.form.get("amount", ""))
                spent = Decimal(request.form.get("spent", "0"))
            except InvalidOperation:
                flash("Enter valid budget values.")
                return redirect(url_for("budgets"))
            name = request.form.get("name", "").strip()
            if not name or amount <= 0 or spent < 0:
                flash("Budget name and amount are required.")
                return redirect(url_for("budgets"))
            db.session.add(
                Budget(
                    user_id=session["user_id"],
                    name=name,
                    amount=amount,
                    spent=spent,
                )
            )
            db.session.commit()
            flash("Budget saved.")
            return redirect(url_for("budgets"))
        rows = [
            budget_row(budget)
            for budget in Budget.query.filter_by(user_id=session["user_id"])
            .order_by(Budget.id.desc())
            .all()
        ]
        return render_template("budgets.html", budgets=rows)
