"""add audit logs and reliability indexes

Revision ID: ab12cd34ef56
Revises: 9c4d2e8b1a77
"""
from alembic import op
import sqlalchemy as sa

revision = "ab12cd34ef56"
down_revision = "9c4d2e8b1a77"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if "audit_logs" not in inspector.get_table_names():
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("action", sa.String(length=80), nullable=False),
            sa.Column("ip_address", sa.String(length=45), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    existing = {index["name"] for index in inspector.get_indexes("transactions")}
    if "ix_transactions_user_date" not in existing:
        op.create_index("ix_transactions_user_date", "transactions", ["user_id", "date"])
    existing = {index["name"] for index in inspector.get_indexes("bills")}
    if "ix_bills_user_due_date" not in existing:
        op.create_index("ix_bills_user_due_date", "bills", ["user_id", "due_date"])


def downgrade():
    op.drop_index("ix_bills_user_due_date", table_name="bills")
    op.drop_index("ix_transactions_user_date", table_name="transactions")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
