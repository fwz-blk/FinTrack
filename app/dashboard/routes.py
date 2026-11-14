from datetime import date
from decimal import Decimal

from flask import render_template, request, session

from ..auth.decorators import login_required
from ..models import Transaction


def register(app):
    @app.get("/dashboard")
    @login_required
    def dashboard():
        period = request.args.get("period", "this_month")
        today = date.today()
        query = Transaction.query.filter_by(user_id=session["user_id"])
        if period == "this_month":
            query = query.filter(Transaction.date >= today.replace(day=1))
        elif period == "this_year":
            query = query.filter(Transaction.date >= today.replace(month=1, day=1))
        elif period != "all_time":
            period = "this_month"
            query = query.filter(Transaction.date >= today.replace(day=1))
        transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        income = sum(
            (t.amount for t in transactions if t.transaction_type == "income"),
            Decimal("0.00"),
        )
        expenses = sum(
            (t.amount for t in transactions if t.transaction_type == "expense"),
            Decimal("0.00"),
        )
        balance = income - expenses
        return render_template(
            "dashboard.html",
            transactions=transactions,
            totals={
                "balance": f"${balance:,.2f}",
                "income": f"${income:,.2f}",
                "expenses": f"${expenses:,.2f}",
                "savings": f"${balance:,.2f}",
            },
            selected_period=period,
            period_label={
                "this_month": "Current month",
                "this_year": "This year",
                "all_time": "All time",
            }[period],
        )
