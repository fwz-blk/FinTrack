from datetime import date
from decimal import Decimal, InvalidOperation

from flask import flash, redirect, render_template, request, session, url_for

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Transaction


def register(app):
    @app.route("/transactions", methods=["GET", "POST"])
    @login_required
    def transactions():
        if request.method == "POST":
            try:
                amount = Decimal(request.form.get("amount", ""))
                transaction_date = date.fromisoformat(request.form.get("date", ""))
            except (InvalidOperation, ValueError):
                flash("Enter a valid amount and date.")
                return redirect(url_for("transactions"))
            transaction_type = request.form.get("transaction_type", "expense")
            category = request.form.get("category", "").strip()
            account = request.form.get("account", "").strip()
            if amount <= 0 or transaction_type not in {"income", "expense"}:
                flash("Enter a valid transaction.")
                return redirect(url_for("transactions"))
            if not category or not account:
                flash("Choose a category and account.")
                return redirect(url_for("transactions"))
            db.session.add(
                Transaction(
                    user_id=session["user_id"],
                    transaction_type=transaction_type,
                    amount=amount,
                    category=category,
                    account=account,
                    date=transaction_date,
                    note=request.form.get("note", "").strip() or None,
                )
            )
            db.session.commit()
            flash("Transaction added.")
            return redirect(url_for("transactions"))

        query = Transaction.query.filter_by(user_id=session["user_id"])
        search = request.args.get("search", "").strip()
        selected_type = request.args.get("type", "")
        selected_category = request.args.get("category", "")
        if search:
            query = query.filter(Transaction.note.ilike(f"%{search}%"))
        if selected_type in {"income", "expense"}:
            query = query.filter_by(transaction_type=selected_type)
        if selected_category:
            query = query.filter_by(category=selected_category)
        transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
        categories = sorted(
            {
                transaction.category
                for transaction in Transaction.query.filter_by(
                    user_id=session["user_id"]
                ).all()
            }
        )
        return render_template(
            "transactions.html",
            transactions=transactions,
            categories=categories,
            search=search,
            selected_type=selected_type,
            selected_category=selected_category,
        )

    @app.post("/transactions/<int:transaction_id>/delete")
    @login_required
    def delete_transaction(transaction_id):
        transaction = Transaction.query.filter_by(
            id=transaction_id, user_id=session["user_id"]
        ).first_or_404()
        db.session.delete(transaction)
        db.session.commit()
        flash("Transaction deleted.")
        return redirect(url_for("transactions"))
