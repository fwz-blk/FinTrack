from datetime import date
from decimal import Decimal

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="USD")
    timezone = db.Column(db.String(64), nullable=False, default="UTC")
    avatar_url = db.Column(db.String(500))
    preferences = db.Column(db.JSON, nullable=False, default=dict)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    reset_token_version = db.Column(db.Integer, nullable=False, default=0)

    transactions = db.relationship(
        "Transaction", back_populates="user", cascade="all, delete-orphan"
    )
    budgets = db.relationship(
        "Budget", back_populates="user", cascade="all, delete-orphan"
    )
    goals = db.relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    goal_contributions = db.relationship(
        "GoalContribution", back_populates="user", cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    accounts = db.relationship(
        "Account", back_populates="user", cascade="all, delete-orphan"
    )
    bills = db.relationship("Bill", back_populates="user", cascade="all, delete-orphan")


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
    recurring = db.Column(db.Boolean, nullable=False, default=False)
    attachment_filename = db.Column(db.String(255))
    bill_id = db.Column(db.Integer, db.ForeignKey("bills.id"))

    user = db.relationship("User", back_populates="transactions")
    bill = db.relationship("Bill", back_populates="transactions")

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


class Category(db.Model):
    __tablename__ = "categories"
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)

    user = db.relationship("User", back_populates="categories")


class Account(db.Model):
    __tablename__ = "accounts"
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)

    user = db.relationship("User", back_populates="accounts")


class Bill(db.Model):
    __tablename__ = "bills"
    __table_args__ = (db.UniqueConstraint("user_id", "name"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    recurrence = db.Column(db.String(20), nullable=False, default="monthly")
    category = db.Column(db.String(80), nullable=False)
    account = db.Column(db.String(80), nullable=False)
    paid = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="bills")
    transactions = db.relationship("Transaction", back_populates="bill")


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    spent = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    category = db.Column(db.String(80), nullable=False, default="All")
    period = db.Column(db.String(20), nullable=False, default="monthly")
    warning_threshold = db.Column(db.Integer, nullable=False, default=80)
    rollover = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="budgets")


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    saved_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    deadline = db.Column(db.Date)
    archived = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", back_populates="goals")
    contributions = db.relationship(
        "GoalContribution", back_populates="goal", cascade="all, delete-orphan"
    )


class GoalContribution(db.Model):
    __tablename__ = "goal_contributions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    goal_id = db.Column(db.Integer, db.ForeignKey("goals.id"), nullable=False)
    transaction_id = db.Column(db.Integer, db.ForeignKey("transactions.id"))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(255))

    user = db.relationship("User", back_populates="goal_contributions")
    goal = db.relationship("Goal", back_populates="contributions")
    transaction = db.relationship("Transaction")
