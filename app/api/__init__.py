from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, render_template, request, session
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from ..extensions import db
from ..models import Bill, Budget, Goal, GoalContribution, Transaction, User
from ..services.bills import generate_due_transactions
from ..services.dashboard import calculate_dashboard, parse_date
from ..services.reports import build_report, parse_report_date


api = Blueprint("api", __name__, url_prefix="/api/v1")


def _response(data=None, errors=None, meta=None, status=200):
    return jsonify({"data": data, "errors": errors or {}, "meta": meta or {}}), status


def _require_user():
    user_id = session.get("user_id")
    if not user_id:
        return None, _response(errors={"authentication": "Login required."}, status=401)
    return db.session.get(User, user_id), None


def _date(value, field):
    try:
        return date.fromisoformat(value), None
    except (TypeError, ValueError):
        return None, {field: "Use YYYY-MM-DD."}


def _decimal(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None, {field: "Enter a valid number."}
    if amount <= 0:
        return None, {field: "Must be greater than zero."}
    return amount, None


def _transaction_data(item):
    return {
        "id": item.id,
        "date": item.date.isoformat(),
        "type": item.transaction_type,
        "amount": str(item.amount),
        "category": item.category,
        "account": item.account,
        "note": item.note,
        "recurring": item.recurring,
        "bill_id": item.bill_id,
    }


def _budget_data(item):
    return {
        "id": item.id,
        "name": item.name,
        "amount": str(item.amount),
        "category": item.category,
        "period": item.period,
        "warning_threshold": item.warning_threshold,
        "rollover": item.rollover,
    }


def _goal_data(item):
    saved = item.saved_amount + sum((entry.amount for entry in item.contributions), Decimal("0.00"))
    return {
        "id": item.id,
        "name": item.name,
        "target_amount": str(item.target_amount),
        "saved_amount": str(saved),
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "archived": item.archived,
    }


def _bill_data(item):
    return {
        "id": item.id,
        "name": item.name,
        "amount": str(item.amount),
        "due_date": item.due_date.isoformat(),
        "recurrence": item.recurrence,
        "category": item.category,
        "account": item.account,
        "paid": item.paid,
    }


@api.before_request
def authenticate_api():
    user, error = _require_user()
    if error:
        return error
    request.current_user = user


@api.get("/transactions")
def list_transactions():
    query = Transaction.query.filter_by(user_id=request.current_user.id)
    if request.args.get("type") in {"income", "expense"}:
        query = query.filter_by(transaction_type=request.args["type"])
    if request.args.get("category"):
        query = query.filter_by(category=request.args["category"])
    if request.args.get("account"):
        query = query.filter_by(account=request.args["account"])
    if request.args.get("search"):
        term = f"%{request.args['search']}%"
        query = query.filter(
            or_(
                Transaction.note.ilike(term),
                Transaction.category.ilike(term),
                Transaction.account.ilike(term),
            )
        )
    if request.args.get("date_from"):
        transaction_date, error = _date(request.args["date_from"], "date_from")
        if error:
            return _response(errors=error, status=422)
        query = query.filter(Transaction.date >= transaction_date)
    if request.args.get("date_to"):
        transaction_date, error = _date(request.args["date_to"], "date_to")
        if error:
            return _response(errors=error, status=422)
        query = query.filter(Transaction.date <= transaction_date)
    items = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    return _response([_transaction_data(item) for item in items])


@api.post("/transactions")
def create_transaction():
    data = request.get_json(silent=True) or {}
    amount, error = _decimal(data.get("amount"), "amount")
    if error:
        return _response(errors=error, status=422)
    transaction_date, error = _date(data.get("date"), "date")
    if error:
        return _response(errors=error, status=422)
    if data.get("type") not in {"income", "expense"}:
        return _response(errors={"type": "Use income or expense."}, status=422)
    if not data.get("category") or not data.get("account"):
        return _response(errors={"category": "Category and account are required."}, status=422)
    item = Transaction(
        user_id=request.current_user.id,
        transaction_type=data["type"],
        amount=amount,
        category=str(data["category"]).strip(),
        account=str(data["account"]).strip(),
        date=transaction_date,
        note=data.get("note"),
        recurring=bool(data.get("recurring", False)),
    )
    db.session.add(item)
    db.session.commit()
    return _response(_transaction_data(item), status=201)


@api.route("/transactions/<int:item_id>", methods=["GET", "PUT", "DELETE"])
def transaction_detail(item_id):
    item = Transaction.query.filter_by(id=item_id, user_id=request.current_user.id).first()
    if item is None:
        return _response(errors={"resource": "Transaction not found."}, status=404)
    if request.method == "GET":
        return _response(_transaction_data(item))
    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return _response({"deleted": True})
    data = request.get_json(silent=True) or {}
    if "amount" in data:
        item.amount, error = _decimal(data["amount"], "amount")
        if error:
            return _response(errors=error, status=422)
    if "date" in data:
        item.date, error = _date(data["date"], "date")
        if error:
            return _response(errors=error, status=422)
    if "type" in data and data["type"] not in {"income", "expense"}:
        return _response(errors={"type": "Use income or expense."}, status=422)
    for key, attribute in (("type", "transaction_type"), ("category", "category"), ("account", "account"), ("note", "note"), ("recurring", "recurring")):
        if key in data:
            setattr(item, attribute, data[key])
    db.session.commit()
    return _response(_transaction_data(item))


@api.get("/budgets")
def list_budgets():
    return _response([_budget_data(item) for item in Budget.query.filter_by(user_id=request.current_user.id).all()])


@api.post("/budgets")
def create_budget():
    data = request.get_json(silent=True) or {}
    amount, error = _decimal(data.get("amount"), "amount")
    if error or not data.get("name"):
        return _response(errors=error or {"name": "Name is required."}, status=422)
    if data.get("period", "monthly") not in {"weekly", "monthly", "yearly"}:
        return _response(errors={"period": "Choose weekly, monthly, or yearly."}, status=422)
    item = Budget(user_id=request.current_user.id, name=data["name"], amount=amount, category=data.get("category", "All"), period=data.get("period", "monthly"), warning_threshold=int(data.get("warning_threshold", 80)), rollover=bool(data.get("rollover", False)))
    db.session.add(item)
    db.session.commit()
    return _response(_budget_data(item), status=201)


@api.route("/budgets/<int:item_id>", methods=["PUT", "DELETE"])
def budget_detail(item_id):
    item = Budget.query.filter_by(id=item_id, user_id=request.current_user.id).first()
    if item is None:
        return _response(errors={"resource": "Budget not found."}, status=404)
    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return _response({"deleted": True})
    data = request.get_json(silent=True) or {}
    for key in ("name", "category", "period", "warning_threshold", "rollover"):
        if key in data:
            setattr(item, key, data[key])
    if "amount" in data:
        item.amount, error = _decimal(data["amount"], "amount")
        if error:
            return _response(errors=error, status=422)
    db.session.commit()
    return _response(_budget_data(item))


@api.get("/goals")
def list_goals():
    return _response([_goal_data(item) for item in Goal.query.filter_by(user_id=request.current_user.id).all()])


@api.post("/goals")
def create_goal():
    data = request.get_json(silent=True) or {}
    target, error = _decimal(data.get("target_amount"), "target_amount")
    if error or not data.get("name"):
        return _response(errors=error or {"name": "Name is required."}, status=422)
    deadline, error = _date(data.get("deadline"), "deadline") if data.get("deadline") else (None, None)
    if error:
        return _response(errors=error, status=422)
    item = Goal(user_id=request.current_user.id, name=data["name"], target_amount=target, saved_amount=Decimal(str(data.get("saved_amount", 0))), deadline=deadline)
    db.session.add(item)
    db.session.commit()
    return _response(_goal_data(item), status=201)


@api.route("/goals/<int:item_id>", methods=["PUT", "DELETE"])
def goal_detail(item_id):
    item = Goal.query.filter_by(id=item_id, user_id=request.current_user.id).first()
    if item is None:
        return _response(errors={"resource": "Goal not found."}, status=404)
    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return _response({"deleted": True})
    data = request.get_json(silent=True) or {}
    for key in ("name", "archived"):
        if key in data:
            setattr(item, key, data[key])
    if "target_amount" in data:
        item.target_amount, error = _decimal(data["target_amount"], "target_amount")
        if error:
            return _response(errors=error, status=422)
    db.session.commit()
    return _response(_goal_data(item))


@api.post("/goals/<int:item_id>/contributions")
def goal_contribution(item_id):
    goal = Goal.query.filter_by(id=item_id, user_id=request.current_user.id).first()
    if goal is None:
        return _response(errors={"resource": "Goal not found."}, status=404)
    data = request.get_json(silent=True) or {}
    amount, error = _decimal(data.get("amount"), "amount")
    if error:
        return _response(errors=error, status=422)
    contribution_date, error = _date(data.get("date"), "date")
    if error:
        return _response(errors=error, status=422)
    item = GoalContribution(user_id=request.current_user.id, goal=goal, amount=amount, date=contribution_date, note=data.get("note"))
    db.session.add(item)
    db.session.commit()
    return _response({"id": item.id, "goal_id": goal.id, "amount": str(amount)}, status=201)


@api.get("/bills")
def list_bills():
    generate_due_transactions(request.current_user.id)
    return _response([_bill_data(item) for item in Bill.query.filter_by(user_id=request.current_user.id).order_by(Bill.due_date).all()])


@api.post("/bills")
def create_bill():
    data = request.get_json(silent=True) or {}
    amount, error = _decimal(data.get("amount"), "amount")
    due_date, date_error = _date(data.get("due_date"), "due_date")
    if error or date_error:
        return _response(errors={**(error or {}), **(date_error or {})}, status=422)
    required = {key: data.get(key) for key in ("name", "category", "account")}
    if any(not value for value in required.values()):
        return _response(errors={key: "Required." for key, value in required.items() if not value}, status=422)
    item = Bill(user_id=request.current_user.id, amount=amount, due_date=due_date, name=data["name"], category=data["category"], account=data["account"], recurrence=data.get("recurrence", "monthly"))
    db.session.add(item)
    db.session.commit()
    return _response(_bill_data(item), status=201)


@api.route("/bills/<int:item_id>", methods=["PUT", "DELETE"])
def bill_detail(item_id):
    item = Bill.query.filter_by(id=item_id, user_id=request.current_user.id).first()
    if item is None:
        return _response(errors={"resource": "Bill not found."}, status=404)
    if request.method == "DELETE":
        db.session.delete(item)
        db.session.commit()
        return _response({"deleted": True})
    data = request.get_json(silent=True) or {}
    for key in ("name", "recurrence", "category", "account", "paid"):
        if key in data:
            setattr(item, key, data[key])
    if "amount" in data:
        item.amount, error = _decimal(data["amount"], "amount")
        if error:
            return _response(errors=error, status=422)
    if "due_date" in data:
        item.due_date, error = _date(data["due_date"], "due_date")
        if error:
            return _response(errors=error, status=422)
    db.session.commit()
    return _response(_bill_data(item))


@api.get("/dashboard")
def api_dashboard():
    data = calculate_dashboard(request.current_user.id, currency=request.current_user.currency, period=request.args.get("period", "this_month"), start=parse_date(request.args.get("start")), end=parse_date(request.args.get("end")))
    data.pop("transactions", None)
    return _response(data)


@api.get("/reports")
def api_reports():
    report = build_report(request.current_user.id, request.args.get("filter", "current_month"), parse_report_date(request.args.get("start")), parse_report_date(request.args.get("end")))
    return _response({
        "filter": report["filter_label"],
        "start": report["start_value"],
        "end": report["end_value"],
        "category": [{"name": name, "amount": str(amount)} for name, amount in report["category"]],
        "account": [{"name": name, "amount": str(amount)} for name, amount in report["account"]],
        "monthly": [{key: str(value) if isinstance(value, Decimal) else value for key, value in row.items()} for row in report["monthly"]],
    })


@api.get("/settings")
def api_settings():
    user = request.current_user
    return _response({"name": user.name, "email": user.email, "currency": user.currency, "timezone": user.timezone, "preferences": user.preferences or {}})


@api.patch("/settings")
def update_settings():
    data = request.get_json(silent=True) or {}
    user = request.current_user
    for key in ("name", "email", "currency", "timezone", "avatar_url", "preferences"):
        if key in data:
            setattr(user, key, data[key])
    db.session.commit()
    return _response({"name": user.name, "email": user.email, "currency": user.currency, "timezone": user.timezone, "preferences": user.preferences or {}})


def register(app):
    app.register_blueprint(api)

    @app.get("/api/docs")
    def api_docs():
        return render_template("api_docs.html")
