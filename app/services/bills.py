import calendar
from datetime import date, timedelta
from decimal import Decimal

from ..extensions import db
from ..models import Bill, Transaction


def next_due_date(value, recurrence):
    if recurrence == "weekly":
        return value + timedelta(days=7)
    if recurrence == "yearly":
        return value.replace(year=value.year + 1)
    month = value.month + 1
    year = value.year + (month > 12)
    month = month if month <= 12 else 1
    return date(year, month, min(value.day, calendar.monthrange(year, month)[1]))


def generate_due_transactions(user_id, today=None):
    today = today or date.today()
    created = 0
    for bill in Bill.query.filter_by(user_id=user_id).all():
        if bill.paid and bill.due_date <= today:
            bill.paid = False
        while bill.due_date <= today and not bill.paid:
            existing = Transaction.query.filter_by(
                user_id=user_id, bill_id=bill.id, date=bill.due_date
            ).first()
            if existing is None:
                db.session.add(
                    Transaction(
                        user_id=user_id,
                        bill=bill,
                        transaction_type="expense",
                        amount=Decimal(bill.amount),
                        category=bill.category,
                        account=bill.account,
                        date=bill.due_date,
                        note=f"Bill: {bill.name}",
                        recurring=True,
                    )
                )
                created += 1
            bill.paid = True
            bill.due_date = next_due_date(bill.due_date, bill.recurrence)
    if created or db.session.dirty:
        db.session.commit()
    return created


def upcoming_bills(user_id, today=None, days=30):
    today = today or date.today()
    return (
        Bill.query.filter(
            Bill.user_id == user_id,
            Bill.due_date <= today + timedelta(days=days),
        )
        .order_by(Bill.due_date)
        .all()
    )
