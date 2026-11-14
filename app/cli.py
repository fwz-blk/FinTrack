from datetime import date
from decimal import Decimal

import click
from werkzeug.security import generate_password_hash

from .extensions import db
from .models import Budget, Goal, Transaction, User


def register_commands(app):
    @app.cli.command("seed-demo")
    def seed_demo():
        """Create a demo account with representative finance data."""
        user = User.query.filter_by(email="demo@fintrack.local").first()
        if user is None:
            user = User(
                name="Demo User",
                email="demo@fintrack.local",
                password_hash=generate_password_hash("demo1234"),
            )
            db.session.add(user)
            db.session.flush()
        if not user.transactions:
            db.session.add_all(
                [
                    Transaction(
                        user_id=user.id,
                        transaction_type="income",
                        amount=Decimal("3200.00"),
                        category="Salary",
                        account="Bank",
                        date=date.today(),
                        note="Monthly salary",
                    ),
                    Transaction(
                        user_id=user.id,
                        transaction_type="expense",
                        amount=Decimal("850.00"),
                        category="Rent",
                        account="Bank",
                        date=date.today(),
                        note="Monthly rent",
                    ),
                    Transaction(
                        user_id=user.id,
                        transaction_type="expense",
                        amount=Decimal("180.50"),
                        category="Food",
                        account="Card",
                        date=date.today(),
                        note="Groceries",
                    ),
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
            db.session.add(
                Goal(
                    user_id=user.id,
                    name="Emergency fund",
                    target_amount=Decimal("5000.00"),
                    saved_amount=Decimal("1800.00"),
                    deadline=date.today().replace(year=date.today().year + 1),
                )
            )
        db.session.commit()
        click.echo("Demo account ready: demo@fintrack.local / demo1234")
