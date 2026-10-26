from datetime import date
from decimal import Decimal

from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    transactions = db.relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    budgets = db.relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    goals = db.relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    account = db.Column(db.String(80), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(255))

    user = db.relationship("User", back_populates="transactions")

    @property
    def type(self):
        return "↓" if self.transaction_type == "income" else "↑"

    @property
    def kind(self):
        return self.transaction_type

    @property
    def amount_display(self):
        sign = "+" if self.transaction_type == "income" else "-"
        return f"{sign}${self.amount:,.2f}"

    @property
    def date_display(self):
        return self.date.strftime("%d %b")


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    spent = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    user = db.relationship("User", back_populates="budgets")


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    saved_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    deadline = db.Column(db.Date)

    user = db.relationship("User", back_populates="goals")
