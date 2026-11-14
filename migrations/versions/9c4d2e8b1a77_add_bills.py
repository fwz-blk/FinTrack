"""add bills and bill-linked transactions

Revision ID: 9c4d2e8b1a77
Revises: 8a943abdbf63
"""
from alembic import op
import sqlalchemy as sa

revision = "9c4d2e8b1a77"
down_revision = "8a943abdbf63"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "bills" not in inspector.get_table_names():
        op.create_table(
            "bills",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("amount", sa.Numeric(10, 2), nullable=False),
            sa.Column("due_date", sa.Date(), nullable=False),
            sa.Column("recurrence", sa.String(length=20), nullable=False, server_default="monthly"),
            sa.Column("category", sa.String(length=80), nullable=False, server_default="Bills"),
            sa.Column("account", sa.String(length=80), nullable=False, server_default="Cash"),
            sa.Column("paid", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("user_id", "name"),
        )
    if "bill_id" not in {column["name"] for column in inspector.get_columns("transactions")}:
        with op.batch_alter_table("transactions") as batch_op:
            batch_op.add_column(sa.Column("bill_id", sa.Integer(), nullable=True))
            batch_op.create_foreign_key("fk_transactions_bill_id", "bills", ["bill_id"], ["id"])


def downgrade():
    with op.batch_alter_table("transactions") as batch_op:
        batch_op.drop_constraint("fk_transactions_bill_id", type_="foreignkey")
        batch_op.drop_column("bill_id")
    op.drop_table("bills")
