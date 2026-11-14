from decimal import Decimal

from flask import render_template, session

from ..auth.decorators import login_required
from ..models import Transaction


def register(app):
    @app.get("/reports")
    @login_required
    def reports():
        totals = {}
        for transaction in Transaction.query.filter_by(user_id=session["user_id"]).all():
            if transaction.transaction_type == "expense":
                totals[transaction.category] = totals.get(
                    transaction.category, Decimal("0.00")
                ) + transaction.amount
        categories = sorted(totals.items(), key=lambda item: item[1], reverse=True)
        maximum = max((amount for _, amount in categories), default=Decimal("1.00"))
        return render_template(
            "reports.html",
            top_categories=[
                (name, amount, int((amount / maximum) * 100))
                for name, amount in categories[:6]
            ],
        )
