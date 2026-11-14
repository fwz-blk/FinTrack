import calendar
import csv
import io
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal

from ..models import Budget, Transaction


def report_range(filter_name="current_month", start=None, end=None, today=None):
    today = today or date.today()
    if start and end:
        return start, end, "Custom dates"
    if filter_name == "previous_month":
        month = today.month - 1 or 12
        year = today.year - (today.month == 1)
        start = date(year, month, 1)
        end = date(year, month, calendar.monthrange(year, month)[1])
        return start, end, "Previous month"
    if filter_name == "current_year":
        return date(today.year, 1, 1), date(today.year, 12, 31), "Current year"
    return today.replace(day=1), today, "Current month"


def parse_report_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def build_report(user_id, filter_name="current_month", start=None, end=None):
    if start and end and start > end:
        start, end = end, start
    start, end, label = report_range(filter_name, start, end)
    transactions = Transaction.query.filter(
        Transaction.user_id == user_id,
        Transaction.date >= start,
        Transaction.date <= end,
    ).order_by(Transaction.date.desc(), Transaction.id.desc()).all()

    category = defaultdict(Decimal)
    account = defaultdict(Decimal)
    months = defaultdict(lambda: {"income": Decimal("0.00"), "expenses": Decimal("0.00")})
    for transaction in transactions:
        if transaction.transaction_type == "expense":
            category[transaction.category] += transaction.amount
            account[transaction.account] += transaction.amount
        key = transaction.date.replace(day=1)
        months[key]["income" if transaction.transaction_type == "income" else "expenses"] += transaction.amount

    monthly = []
    current = start.replace(day=1)
    last = end.replace(day=1)
    while current <= last:
        values = months[current]
        monthly.append(
            {
                "month": current.strftime("%b %Y"),
                "income": values["income"],
                "expenses": values["expenses"],
                "savings": values["income"] - values["expenses"],
            }
        )
        current = (
            date(current.year + 1, 1, 1)
            if current.month == 12
            else date(current.year, current.month + 1, 1)
        )

    budget_performance = []
    for budget in Budget.query.filter_by(user_id=user_id).all():
        spent = sum(
            (
                transaction.amount
                for transaction in transactions
                if transaction.transaction_type == "expense"
                and (budget.category == "All" or transaction.category == budget.category)
            ),
            Decimal("0.00"),
        )
        limit = Decimal(budget.amount)
        budget_performance.append(
            {
                "name": budget.name,
                "category": budget.category,
                "limit": limit,
                "spent": spent,
                "percent": int(spent / limit * 100) if limit else 0,
            }
        )

    return {
        "filter_name": filter_name,
        "filter_label": label,
        "start": start,
        "end": end,
        "start_value": start.isoformat(),
        "end_value": end.isoformat(),
        "transactions": transactions,
        "category": sorted(category.items(), key=lambda item: item[1], reverse=True),
        "account": sorted(account.items(), key=lambda item: item[1], reverse=True),
        "monthly": monthly,
        "budget_performance": budget_performance,
        "income": sum((item["income"] for item in monthly), Decimal("0.00")),
        "expenses": sum((item["expenses"] for item in monthly), Decimal("0.00")),
    }


def report_csv(report):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["FinTrack report", report["filter_label"]])
    writer.writerow(["Date range", report["start_value"], report["end_value"]])
    writer.writerow([])
    writer.writerow(["Category breakdown", "Amount"])
    writer.writerows(report["category"])
    writer.writerow([])
    writer.writerow(["Account breakdown", "Amount"])
    writer.writerows(report["account"])
    writer.writerow([])
    writer.writerow(["Month", "Income", "Expenses", "Savings"])
    for row in report["monthly"]:
        writer.writerow([row["month"], row["income"], row["expenses"], row["savings"]])
    writer.writerow([])
    writer.writerow(["Budget", "Category", "Limit", "Spent", "Percent"])
    for row in report["budget_performance"]:
        writer.writerow([row["name"], row["category"], row["limit"], row["spent"], row["percent"]])
    return output.getvalue()


def report_pdf(report):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph

    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=letter, rightMargin=0.5 * inch, leftMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("FinTrack Report", styles["Title"]),
        Paragraph(f"{report['filter_label']}: {report['start_value']} to {report['end_value']}", styles["Normal"]),
        Spacer(1, 12),
    ]

    def add_table(title, rows):
        story.append(Paragraph(title, styles["Heading2"]))
        story.append(Table(rows, style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ])))
        story.append(Spacer(1, 10))

    add_table("Summary", [["Metric", "Amount"], ["Income", str(report["income"])], ["Expenses", str(report["expenses"])], ["Savings", str(report["income"] - report["expenses"])]])
    add_table("Category breakdown", [["Category", "Amount"]] + [[name, str(amount)] for name, amount in report["category"]])
    add_table("Account breakdown", [["Account", "Amount"]] + [[name, str(amount)] for name, amount in report["account"]])
    add_table("Monthly comparison and savings trend", [["Month", "Income", "Expenses", "Savings"]] + [[row["month"], str(row["income"]), str(row["expenses"]), str(row["savings"])] for row in report["monthly"]])
    add_table("Budget performance", [["Budget", "Category", "Limit", "Spent", "Percent"]] + [[row["name"], row["category"], str(row["limit"]), str(row["spent"]), f"{row['percent']}%"] for row in report["budget_performance"]])
    document.build(story)
    return output.getvalue()
