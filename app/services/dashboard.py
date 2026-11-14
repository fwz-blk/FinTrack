import calendar
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from ..models import Budget, Goal, Transaction
from .budgets import period_bounds


PERIODS = {
    "this_week": "Current week",
    "this_month": "Current month",
    "this_year": "This year",
    "all_time": "All time",
}


def _month_start(value):
    return value.replace(day=1)


def _month_end(value):
    return value.replace(day=calendar.monthrange(value.year, value.month)[1])


def dashboard_range(period, start=None, end=None, today=None):
    today = today or date.today()
    if start and end:
        return start, end, "Custom range"
    if period == "this_week":
        start, end = period_bounds("weekly", today)
    elif period == "this_year":
        start, end = date(today.year, 1, 1), date(today.year, 12, 31)
    elif period == "all_time":
        return None, None, PERIODS["all_time"]
    else:
        period = "this_month"
        start, end = _month_start(today), _month_end(today)
    return start, end, PERIODS[period]


def _currency_symbol(currency):
    return {"EUR": "€", "GBP": "£", "INR": "₹"}.get(currency, "$")


def _money(amount, symbol):
    return f"{symbol}{amount:,.2f}"


def _month_series(transactions, start, end):
    if not transactions:
        return []
    first = _month_start(start or min(item.date for item in transactions))
    last = _month_start(end or max(item.date for item in transactions))
    values = defaultdict(lambda: {"income": Decimal("0.00"), "expenses": Decimal("0.00")})
    for transaction in transactions:
        key = _month_start(transaction.date)
        values[key][
            "income" if transaction.transaction_type == "income" else "expenses"
        ] += transaction.amount
    result = []
    current = first
    while current <= last:
        result.append(
            {
                "label": current.strftime("%b %Y"),
                "income": float(values[current]["income"]),
                "expenses": float(values[current]["expenses"]),
            }
        )
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )
    return result


def calculate_dashboard(user_id, currency="USD", period="this_month", start=None, end=None):
    if start and end and start > end:
        start, end = end, start
    if not (start and end) and period not in PERIODS:
        period = "this_month"
    start, end, period_label = dashboard_range(period, start, end)
    query = Transaction.query.filter_by(user_id=user_id)
    if start:
        query = query.filter(Transaction.date >= start, Transaction.date <= end)
    transactions = query.order_by(Transaction.date.desc(), Transaction.id.desc()).all()
    income = sum(
        (item.amount for item in transactions if item.transaction_type == "income"),
        Decimal("0.00"),
    )
    expenses = sum(
        (item.amount for item in transactions if item.transaction_type == "expense"),
        Decimal("0.00"),
    )
    balance = income - expenses
    savings_rate = (balance / income * 100) if income else Decimal("0.00")
    symbol = _currency_symbol(currency)

    categories = defaultdict(Decimal)
    for item in transactions:
        if item.transaction_type == "expense":
            categories[item.category] += item.amount
    category_total = sum(categories.values(), Decimal("0.00"))
    category_data = [
        {
            "name": name,
            "amount": _money(amount, symbol),
            "percent": int(amount / category_total * 100) if category_total else 0,
        }
        for name, amount in sorted(categories.items(), key=lambda entry: entry[1], reverse=True)
    ]

    budgets = []
    for budget in Budget.query.filter_by(user_id=user_id).all():
        spent = sum(
            (
                item.amount
                for item in transactions
                if item.transaction_type == "expense"
                and (budget.category == "All" or item.category == budget.category)
            ),
            Decimal("0.00"),
        )
        limit = Decimal(budget.amount)
        percent = int(spent / limit * 100) if limit else 0
        if percent >= budget.warning_threshold:
            budgets.append(
                {
                    "name": budget.name,
                    "percent": percent,
                    "tone": "red" if percent >= 100 else "orange",
                }
            )

    goals = []
    for goal in Goal.query.filter_by(user_id=user_id, archived=False).all():
        contributions = sum(
            (
                contribution.amount
                for contribution in goal.contributions
                if not start or start <= contribution.date <= end
            ),
            Decimal("0.00"),
        )
        saved = goal.saved_amount + contributions
        percent = int(saved / goal.target_amount * 100) if goal.target_amount else 0
        goals.append({"name": goal.name, "percent": min(100, percent)})

    monthly_data = _month_series(transactions, start, end)
    return {
        "period": period,
        "period_label": period_label,
        "start": start,
        "end": end,
        "has_data": bool(transactions),
        "transactions": transactions,
        "totals": {
            "balance": _money(balance, symbol),
            "income": _money(income, symbol),
            "expenses": _money(expenses, symbol),
            "savings_rate": f"{savings_rate:.1f}%",
        },
        "category_data": category_data,
        "monthly_data": monthly_data,
        "chart_max": max(
            (
                max(item["income"], item["expenses"])
                for item in monthly_data
            ),
            default=0,
        ),
        "budget_warnings": budgets,
        "goal_progress": goals,
    }


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None
