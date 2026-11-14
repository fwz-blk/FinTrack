import csv
import io
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import (
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from ..auth.decorators import login_required
from ..extensions import db
from ..models import Account, Category, Transaction

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}


def _parse_transaction(form, file_storage=None):
    try:
        amount = Decimal(form.get("amount", ""))
        transaction_date = date.fromisoformat(form.get("date", ""))
    except (InvalidOperation, ValueError):
        raise ValueError("Enter a valid amount and date.") from None
    transaction_type = form.get("transaction_type", "expense")
    category = form.get("category", "").strip()
    account = form.get("account", "").strip()
    if amount <= 0 or transaction_type not in {"income", "expense"}:
        raise ValueError("Enter a valid transaction.")
    if not category or not account:
        raise ValueError("Choose a category and account.")
    attachment_filename = None
    if file_storage and file_storage.filename:
        original_name = secure_filename(file_storage.filename)
        extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
        if extension not in ALLOWED_EXTENSIONS:
            raise ValueError("Attachments must be PDF, PNG, JPG, JPEG, or WEBP files.")
        attachment_filename = original_name
    return {
        "transaction_type": transaction_type,
        "amount": amount,
        "category": category,
        "account": account,
        "date": transaction_date,
        "note": form.get("note", "").strip() or None,
        "recurring": form.get("recurring") == "on",
        "attachment_filename": attachment_filename,
    }


def _save_attachment(file_storage, user_id, filename):
    directory = Path(current_app.instance_path) / "uploads" / str(user_id)
    directory.mkdir(parents=True, exist_ok=True)
    file_storage.save(directory / filename)


def _query_transactions():
    query = Transaction.query.filter_by(user_id=session["user_id"])
    search = request.args.get("search", "").strip()
    selected_type = request.args.get("type", "")
    selected_category = request.args.get("category", "")
    selected_account = request.args.get("account", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    min_amount = request.args.get("min_amount", "")
    max_amount = request.args.get("max_amount", "")
    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Transaction.note.ilike(term),
                Transaction.category.ilike(term),
                Transaction.account.ilike(term),
            )
        )
    if selected_type in {"income", "expense"}:
        query = query.filter_by(transaction_type=selected_type)
    if selected_category:
        query = query.filter_by(category=selected_category)
    if selected_account:
        query = query.filter_by(account=selected_account)
    try:
        if date_from:
            query = query.filter(Transaction.date >= date.fromisoformat(date_from))
        if date_to:
            query = query.filter(Transaction.date <= date.fromisoformat(date_to))
        if min_amount:
            query = query.filter(Transaction.amount >= Decimal(min_amount))
        if max_amount:
            query = query.filter(Transaction.amount <= Decimal(max_amount))
    except (InvalidOperation, ValueError):
        flash("Some filters were invalid and were ignored.")
    return query


def register(app):
    @app.route("/transactions", methods=["GET", "POST"])
    @login_required
    def transactions():
        if request.method == "POST":
            try:
                values = _parse_transaction(request.form, request.files.get("attachment"))
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("transactions"))
            transaction = Transaction(user_id=session["user_id"], **values)
            db.session.add(transaction)
            db.session.commit()
            attachment = request.files.get("attachment")
            if values["attachment_filename"] and attachment:
                _save_attachment(attachment, transaction.user_id, values["attachment_filename"])
            flash("Transaction added.")
            return redirect(url_for("transactions"))

        query = _query_transactions()
        page = request.args.get("page", 1, type=int)
        pagination = query.order_by(
            Transaction.date.desc(), Transaction.id.desc()
        ).paginate(page=max(1, page), per_page=10, error_out=False)
        user_id = session["user_id"]
        categories = sorted(
            {category.name for category in Category.query.filter_by(user_id=user_id)}
            | {
                transaction.category
                for transaction in Transaction.query.filter_by(user_id=user_id)
            }
        )
        accounts = sorted(
            {account.name for account in Account.query.filter_by(user_id=user_id)}
            | {
                transaction.account
                for transaction in Transaction.query.filter_by(user_id=user_id)
            }
        )
        return render_template(
            "transactions.html",
            transactions=pagination.items,
            pagination=pagination,
            categories=categories,
            accounts=accounts,
            search=request.args.get("search", ""),
            selected_type=request.args.get("type", ""),
            selected_category=request.args.get("category", ""),
            selected_account=request.args.get("account", ""),
            date_from=request.args.get("date_from", ""),
            date_to=request.args.get("date_to", ""),
            min_amount=request.args.get("min_amount", ""),
            max_amount=request.args.get("max_amount", ""),
        )

    @app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
    @login_required
    def edit_transaction(transaction_id):
        transaction = Transaction.query.filter_by(
            id=transaction_id, user_id=session["user_id"]
        ).first_or_404()
        if request.method == "POST":
            try:
                values = _parse_transaction(request.form, request.files.get("attachment"))
            except ValueError as error:
                flash(str(error))
                return redirect(url_for("edit_transaction", transaction_id=transaction.id))
            for key, value in values.items():
                if value is not None:
                    setattr(transaction, key, value)
            db.session.commit()
            attachment = request.files.get("attachment")
            if values["attachment_filename"] and attachment:
                _save_attachment(attachment, transaction.user_id, values["attachment_filename"])
            flash("Transaction updated.")
            return redirect(url_for("transactions"))
        return render_template(
            "transaction_edit.html",
            transaction=transaction,
            categories=sorted(
                category.name
                for category in Category.query.filter_by(user_id=session["user_id"])
            ),
            accounts=sorted(
                account.name
                for account in Account.query.filter_by(user_id=session["user_id"])
            ),
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

    @app.post("/transactions/bulk-delete")
    @login_required
    def bulk_delete_transactions():
        ids = request.form.getlist("transaction_ids")
        if ids:
            Transaction.query.filter(
                Transaction.user_id == session["user_id"], Transaction.id.in_(ids)
            ).delete(synchronize_session=False)
            db.session.commit()
            flash(f"{len(ids)} transaction(s) deleted.")
        return redirect(url_for("transactions"))

    @app.get("/transactions/export")
    @login_required
    def export_transactions():
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["date", "type", "amount", "category", "account", "note", "recurring"])
        for transaction in _query_transactions().order_by(Transaction.date.desc()).all():
            writer.writerow(
                [
                    transaction.date.isoformat(),
                    transaction.transaction_type,
                    transaction.amount,
                    transaction.category,
                    transaction.account,
                    transaction.note or "",
                    transaction.recurring,
                ]
            )
        response = app.response_class(output.getvalue(), mimetype="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
        return response

    @app.post("/transactions/import")
    @login_required
    def import_transactions():
        uploaded = request.files.get("file")
        if not uploaded or not uploaded.filename:
            flash("Choose a CSV file to import.")
            return redirect(url_for("transactions"))
        created = skipped = 0
        try:
            rows = csv.DictReader(io.TextIOWrapper(uploaded.stream, encoding="utf-8-sig"))
            required = {"date", "type", "amount", "category", "account"}
            if not required.issubset(set(rows.fieldnames or [])):
                raise ValueError("CSV must include date, type, amount, category, and account columns.")
            for row in rows:
                try:
                    values = _parse_transaction(
                        {
                            "date": row["date"],
                            "transaction_type": row["type"],
                            "amount": row["amount"],
                            "category": row["category"],
                            "account": row["account"],
                            "note": row.get("note", ""),
                            "recurring": row.get("recurring", "").lower() == "true",
                        }
                    )
                except (KeyError, ValueError, InvalidOperation):
                    skipped += 1
                    continue
                duplicate = Transaction.query.filter_by(
                    user_id=session["user_id"],
                    date=values["date"],
                    transaction_type=values["transaction_type"],
                    amount=values["amount"],
                    category=values["category"],
                    account=values["account"],
                    note=values["note"],
                ).first()
                if duplicate:
                    skipped += 1
                    continue
                db.session.add(Transaction(user_id=session["user_id"], **values))
                created += 1
            db.session.commit()
        except (UnicodeDecodeError, csv.Error, ValueError) as error:
            db.session.rollback()
            flash(str(error))
            return redirect(url_for("transactions"))
        flash(f"Imported {created} transaction(s); skipped {skipped}.")
        return redirect(url_for("transactions"))

    @app.post("/transactions/categories")
    @login_required
    def create_category():
        name = request.form.get("name", "").strip()
        if name and not Category.query.filter_by(user_id=session["user_id"], name=name).first():
            db.session.add(Category(user_id=session["user_id"], name=name))
            db.session.commit()
            flash("Category added.")
        return redirect(url_for("transactions"))

    @app.post("/transactions/accounts")
    @login_required
    def create_account():
        name = request.form.get("name", "").strip()
        if name and not Account.query.filter_by(user_id=session["user_id"], name=name).first():
            db.session.add(Account(user_id=session["user_id"], name=name))
            db.session.commit()
            flash("Account added.")
        return redirect(url_for("transactions"))

    @app.get("/transactions/<int:transaction_id>/attachment")
    @login_required
    def transaction_attachment(transaction_id):
        transaction = Transaction.query.filter_by(
            id=transaction_id, user_id=session["user_id"]
        ).first_or_404()
        if not transaction.attachment_filename:
            return ("Attachment not found", 404)
        directory = Path(current_app.instance_path) / "uploads" / str(session["user_id"])
        return send_from_directory(directory, transaction.attachment_filename)
