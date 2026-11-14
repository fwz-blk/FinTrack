from datetime import date, timedelta
from decimal import Decimal

import click
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import Bill, Budget, Goal, GoalContribution, Transaction, User


def register_commands(app):
    @app.cli.command("seed-demo")
    def seed_demo():
        """Create a demo account with representative finance data."""
        demo_password = "DemoFinance2026!"
        user = User.query.filter_by(email="demo@fintrack.local").first()
        if user is None:
            user = User(
                name="Demo User",
                email="demo@fintrack.local",
                password_hash=generate_password_hash(demo_password),
            )
            db.session.add(user)
            db.session.flush()
        user.password_hash = generate_password_hash(demo_password)
        user.email_verified = True
        today = date.today()
        if len(user.transactions) < 10:
            db.session.add_all(
                [
                    Transaction(
                        user_id=user.id,
                        transaction_type="income",
                        amount=Decimal("3200.00"),
                        category="Salary",
                        account="Bank",
                        date=today,
                        note="Monthly salary",
                    ),
                    Transaction(
                        user_id=user.id,
                        transaction_type="expense",
                        amount=Decimal("850.00"),
                        category="Rent",
                        account="Bank",
                        date=today.replace(day=1),
                        note="Monthly rent",
                    ),
                    Transaction(
                        user_id=user.id,
                        transaction_type="expense",
                        amount=Decimal("180.50"),
                        category="Food",
                        account="Card",
                        date=today - timedelta(days=2),
                        note="Groceries",
                    ),
                    Transaction(user_id=user.id, transaction_type="expense", amount=Decimal("65.00"), category="Transport", account="Card", date=today - timedelta(days=4), note="Metro and taxi"),
                    Transaction(user_id=user.id, transaction_type="expense", amount=Decimal("42.00"), category="Subscriptions", account="Card", date=today - timedelta(days=7), note="Streaming services"),
                    Transaction(user_id=user.id, transaction_type="income", amount=Decimal("450.00"), category="Freelance", account="Savings", date=today - timedelta(days=12), note="Design project"),
                    Transaction(user_id=user.id, transaction_type="expense", amount=Decimal("120.00"), category="Shopping", account="Card", date=today - timedelta(days=15), note="Household supplies"),
                    Transaction(user_id=user.id, transaction_type="expense", amount=Decimal("75.00"), category="Food", account="Card", date=today - timedelta(days=18), note="Dinner with friends"),
                    Transaction(user_id=user.id, transaction_type="expense", amount=Decimal("35.00"), category="Health", account="Bank", date=today - timedelta(days=22), note="Pharmacy"),
                    Transaction(user_id=user.id, transaction_type="income", amount=Decimal("300.00"), category="Bonus", account="Bank", date=today - timedelta(days=25), note="Performance bonus"),
                ]
            )
        if not user.budgets:
            db.session.add(
                Budget(
                    user_id=user.id,
                    name="Food",
                    amount=Decimal("400.00"),
                    spent=Decimal("180.50"),
                )
            )
        if not user.goals:
            goal = Goal(
                    user_id=user.id,
                    name="Emergency fund",
                    target_amount=Decimal("5000.00"),
                    saved_amount=Decimal("1800.00"),
                    deadline=today.replace(year=today.year + 1),
                )
            db.session.add(goal)
            db.session.flush()
        if not GoalContribution.query.filter_by(user_id=user.id).first():
            goal = user.goals[0]
            db.session.add(GoalContribution(user_id=user.id, goal_id=goal.id, amount=Decimal("350.00"), date=today - timedelta(days=10), note="Automatic savings transfer"))
        if not user.bills:
            db.session.add_all(
                [
                    Bill(user_id=user.id, name="Internet", amount=Decimal("60.00"), due_date=today + timedelta(days=5), recurrence="monthly", category="Bills", account="Bank"),
                    Bill(user_id=user.id, name="Gym membership", amount=Decimal("35.00"), due_date=today + timedelta(days=12), recurrence="monthly", category="Health", account="Card"),
                ]
            )
        db.session.commit()
        click.echo(f"Demo account ready: demo@fintrack.local / {demo_password}")
