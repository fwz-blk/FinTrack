from flask import render_template, request, session

from ..auth.decorators import login_required
from ..extensions import db
from ..models import User
from ..services.bills import generate_due_transactions, upcoming_bills
from ..services.dashboard import calculate_dashboard, parse_date


def register(app):
    @app.get("/dashboard")
    @login_required
    def dashboard():
        period = request.args.get("period", "this_month")
        generate_due_transactions(session["user_id"])
        dashboard = calculate_dashboard(
            session["user_id"],
            currency=db.session.get(User, session["user_id"]).currency,
            period=period,
            start=parse_date(request.args.get("start")),
            end=parse_date(request.args.get("end")),
        )
        return render_template(
            "dashboard.html",
            **dashboard,
            upcoming_bills=upcoming_bills(session["user_id"]),
            selected_period=dashboard["period"],
            start_value=request.args.get("start", ""),
            end_value=request.args.get("end", ""),
        )
