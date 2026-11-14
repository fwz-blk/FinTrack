from datetime import date
from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Account, Bill, Category, Transaction
from ..services.bills import generate_due_transactions


def register(app):
    @app.get("/")
    def landing():
        return render_template("landing.html")

    @app.get("/features")
    def features():
        return render_template("features.html")

    @app.get("/about")
    def about():
        return render_template("about.html")

    @app.get("/help")
    def help_page():
        return render_template("info.html", page_title="Help", heading="How can we help?", body="Use the dashboard to review your money, Transactions to manage entries, Budgets for limits, and Goals for savings targets. For account help, email support@fintrack.com.")

    @app.get("/terms")
    def terms():
        return render_template("info.html", page_title="Terms of Service", heading="Terms of Service", body="FinTrack is a student project for personal finance tracking. You are responsible for the accuracy of data you enter and should keep your account credentials private.")

    @app.get("/privacy")
    def privacy():
        return render_template("info.html", page_title="Privacy Policy", heading="Privacy Policy", body="FinTrack stores your account and finance records for your use. Records are scoped to your account and are not shown to other users. You can export, anonymize, or delete your data from Settings.")

    @app.route("/bills", methods=["GET", "POST"])
    @login_required
    def bills():
        if request.method == "POST":
            try:
                amount = Decimal(request.form.get("amount", ""))
                due_date = date.fromisoformat(request.form.get("due_date", ""))
            except (InvalidOperation, ValueError):
                flash("Enter a valid bill amount and due date.")
                return redirect(url_for("bills"))
            recurrence = request.form.get("recurrence", "monthly")
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "").strip()
            account = request.form.get("account", "").strip()
            if not name or amount <= 0 or not category or not account:
                flash("Complete all bill fields.")
            elif recurrence not in {"weekly", "monthly", "yearly"}:
                flash("Choose a valid recurrence.")
            elif Bill.query.filter_by(user_id=session["user_id"], name=name).first():
                flash("A bill with that name already exists.")
            else:
                db.session.add(
                    Bill(
                        user_id=session["user_id"],
                        name=name,
                        amount=amount,
                        due_date=due_date,
                        recurrence=recurrence,
                        category=category,
                        account=account,
                    )
                )
                db.session.commit()
                flash("Bill saved.")
            return redirect(url_for("bills"))
        user_id = session["user_id"]
        return render_template(
            "bills.html",
            bills=Bill.query.filter_by(user_id=user_id).order_by(Bill.due_date).all(),
            categories=sorted({item.name for item in Category.query.filter_by(user_id=user_id)} | {item.category for item in Transaction.query.filter_by(user_id=user_id)}),
            accounts=sorted({item.name for item in Account.query.filter_by(user_id=user_id)} | {item.account for item in Transaction.query.filter_by(user_id=user_id)}),
            today=date.today(),
        )

    @app.post("/bills/<int:bill_id>/paid")
    @login_required
    def toggle_bill_paid(bill_id):
        bill = Bill.query.filter_by(id=bill_id, user_id=session["user_id"]).first_or_404()
        bill.paid = not bill.paid
        db.session.commit()
        flash("Bill status updated.")
        return redirect(url_for("bills"))

    @app.post("/bills/<int:bill_id>/delete")
    @login_required
    def delete_bill(bill_id):
        bill = Bill.query.filter_by(id=bill_id, user_id=session["user_id"]).first_or_404()
        db.session.delete(bill)
        db.session.commit()
        flash("Bill deleted.")
        return redirect(url_for("bills"))
