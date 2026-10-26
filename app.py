from datetime import date
from decimal import Decimal, InvalidOperation
from functools import wraps
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db

app = Flask(__name__)
app.config["SECRET_KEY"] = "prototype-secret-key"
Path(app.instance_path).mkdir(parents=True, exist_ok=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(
    Path(app.instance_path) / "finance.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

from models import Budget, Goal, Transaction, User  # noqa: F401

with app.app_context():
    db.create_all()


def _budget_row(budget):
    total = float(budget.amount)
    spent = float(budget.spent)
    percent = 0 if total <= 0 else min(100, int((spent / total) * 100))
    if percent >= 100:
        tone = "red" if spent > total else "green"
    elif percent >= 80:
        tone = "orange"
    else:
        tone = "green"
    remaining = max(0.0, total - spent)
    status = "Over budget" if spent > total else "Near limit" if percent >= 80 else "On track"
    return {
        "name": budget.name,
        "spent": f"${spent:,.2f} / ${total:,.2f}",
        "percent": percent,
        "tone": tone,
        "remaining": remaining,
        "status": status,
    }


def _goal_row(goal):
    target = float(goal.target_amount)
    saved = float(goal.saved_amount)
    percent = 0 if target <= 0 else min(100, int((saved / target) * 100))
    tone = "green" if percent >= 100 else "blue" if percent >= 50 else ""
    deadline = goal.deadline.strftime("%b %d, %Y") if goal.deadline else "No deadline"
    return {
        "name": goal.name,
        "deadline": deadline,
        "percent": f"{percent}%",
        "amount": f"${saved:,.2f} / ${target:,.2f}",
        "tone": tone,
        "complete": percent >= 100,
    }


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


@app.context_processor
def shared_context():
    return {
        "implemented_pages": {"dashboard", "transactions", "budgets", "goals", "reports", "settings"},
        "nav_items": [
            ("dashboard", "◉", "Dashboard"),
            ("transactions", "⇄", "Transactions"),
            ("budgets", "◔", "Budgets"),
            ("goals", "◎", "Goals"),
            ("bills", "⟳", "Bills"),
            ("reports", "⌁", "Reports"),
        ]
    }


@app.get("/")
def landing():
    return render_template("landing.html")


@app.get("/features")
def features():
    return render_template("features.html")


@app.get("/about")
def about():
    return render_template("about.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if user is None or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.")
            return render_template("login.html"), 401

        session["user_id"] = user.id
        session["user_name"] = user.name
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please complete all required fields.")
            return render_template("register.html"), 400
        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html"), 400
        if User.query.filter_by(email=email).first() is not None:
            flash("An account with that email already exists.")
            return render_template("register.html"), 409

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        session["user_id"] = user.id
        session["user_name"] = user.name
        return redirect(url_for("dashboard"))

    return render_template("register.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.get("/dashboard")
@login_required
def dashboard():
    period = request.args.get("period", "this_month")
    today = date.today()
    transaction_query = Transaction.query.filter_by(user_id=session["user_id"])

    if period == "this_month":
        start_date = today.replace(day=1)
        transaction_query = transaction_query.filter(Transaction.date >= start_date)
    elif period == "this_year":
        start_date = today.replace(month=1, day=1)
        transaction_query = transaction_query.filter(Transaction.date >= start_date)
    elif period != "all_time":
        period = "this_month"
        start_date = today.replace(day=1)
        transaction_query = transaction_query.filter(Transaction.date >= start_date)

    user_transactions = transaction_query.order_by(
        Transaction.date.desc(), Transaction.id.desc()
    ).all()
    income_total = sum((t.amount for t in user_transactions if t.transaction_type == "income"), Decimal("0.00"))
    expense_total = sum((t.amount for t in user_transactions if t.transaction_type == "expense"), Decimal("0.00"))
    balance_total = income_total - expense_total
    summary = {
        "balance": f"${balance_total:,.2f}",
        "income": f"${income_total:,.2f}",
        "expenses": f"${expense_total:,.2f}",
        "savings": f"${balance_total:,.2f}",
    }
    period_labels = {
        "this_month": "Current month",
        "this_year": "This year",
        "all_time": "All time",
    }
    return render_template(
        "dashboard.html",
        transactions=user_transactions,
        totals=summary,
        selected_period=period,
        period_label=period_labels[period],
    )


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
        note = request.form.get("note", "").strip()

        if amount <= 0 or transaction_type not in {"income", "expense"}:
            flash("Enter a valid transaction.")
            return redirect(url_for("transactions"))
        if not category or not account:
            flash("Choose a category and account.")
            return redirect(url_for("transactions"))

        transaction = Transaction(
            user_id=session["user_id"],
            transaction_type=transaction_type,
            amount=amount,
            category=category,
            account=account,
            date=transaction_date,
            note=note or None,
        )
        db.session.add(transaction)
        db.session.commit()
        flash("Transaction added.")
        return redirect(url_for("transactions"))

    user_transactions = (
        Transaction.query.filter_by(user_id=session["user_id"])
        .order_by(Transaction.date.desc(), Transaction.id.desc())
        .all()
    )
    return render_template("transactions.html", transactions=user_transactions)


@app.route("/budgets", methods=["GET", "POST"])
@login_required
def budgets():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        amount = request.form.get("amount", "")
        spent = request.form.get("spent", "0")
        try:
            amount_decimal = Decimal(amount)
            spent_decimal = Decimal(spent)
        except InvalidOperation:
            flash("Enter valid budget values.")
            return redirect(url_for("budgets"))
        if not name or amount_decimal <= 0:
            flash("Budget name and amount are required.")
            return redirect(url_for("budgets"))

        budget = Budget(
            user_id=session["user_id"],
            name=name,
            amount=amount_decimal,
            spent=spent_decimal,
        )
        db.session.add(budget)
        db.session.commit()
        flash("Budget saved.")
        return redirect(url_for("budgets"))

    budgets = [
        _budget_row(b)
        for b in Budget.query.filter_by(user_id=session["user_id"]).order_by(Budget.id.desc()).all()
    ]
    return render_template("budgets.html", budgets=budgets)


@app.route("/goals", methods=["GET", "POST"])
@login_required
def goals():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        target_amount = request.form.get("target_amount", "")
        saved_amount = request.form.get("saved_amount", "0")
        deadline = request.form.get("deadline") or None
        try:
            target_decimal = Decimal(target_amount)
            saved_decimal = Decimal(saved_amount)
        except InvalidOperation:
            flash("Enter valid goal values.")
            return redirect(url_for("goals"))
        if not name or target_decimal <= 0:
            flash("Goal name and target amount are required.")
            return redirect(url_for("goals"))

        goal = Goal(
            user_id=session["user_id"],
            name=name,
            target_amount=target_decimal,
            saved_amount=saved_decimal,
            deadline=date.fromisoformat(deadline) if deadline else None,
        )
        db.session.add(goal)
        db.session.commit()
        flash("Goal saved.")
        return redirect(url_for("goals"))

    goals = [
        _goal_row(g)
        for g in Goal.query.filter_by(user_id=session["user_id"]).order_by(Goal.id.desc()).all()
    ]
    return render_template("goals.html", goals=goals)


@app.get("/reports")
@login_required
def reports():
    return render_template("reports.html")


@app.get("/settings")
@login_required
def settings():
    return render_template("settings.html")


if __name__ == "__main__":
    app.run(debug=True)
