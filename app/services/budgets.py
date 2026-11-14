import calendar
from datetime import date, timedelta
from decimal import Decimal

from ..models import Transaction


def period_bounds(period, reference=None, offset=0):
    reference = reference or date.today()
    if period == "weekly":
        start = reference - timedelta(days=reference.weekday()) + timedelta(days=offset * 7)
        return start, start + timedelta(days=6)
    if period == "yearly":
        year = reference.year + offset
        return date(year, 1, 1), date(year, 12, 31)
    month_index = reference.year * 12 + reference.month - 1 + offset
    year, month = divmod(month_index, 12)
    start = date(year, month + 1, 1)
    return start, date(year, month + 1, calendar.monthrange(year, month + 1)[1])


def spent_for_budget(budget, user_id, reference=None):
    start, end = period_bounds(budget.period, reference)
    query = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.transaction_type == "expense",
        Transaction.date >= start,
        Transaction.date <= end,
    )
    if budget.category != "All":
        query = query.filter(Transaction.category == budget.category)
    spent = sum((transaction.amount for transaction in query.all()), Decimal("0.00"))
    limit = Decimal(budget.amount)
    if budget.rollover:
        previous_start, previous_end = period_bounds(budget.period, reference, -1)
        previous_query = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "expense",
            Transaction.date >= previous_start,
            Transaction.date <= previous_end,
        )
        if budget.category != "All":
            previous_query = previous_query.filter(Transaction.category == budget.category)
        previous_spent = sum(
            (transaction.amount for transaction in previous_query.all()), Decimal("0.00")
        )
        limit += max(Decimal("0.00"), Decimal(budget.amount) - previous_spent)
    return spent, limit
