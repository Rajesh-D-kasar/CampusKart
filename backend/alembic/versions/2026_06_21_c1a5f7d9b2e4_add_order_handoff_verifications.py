"""add order handoff verifications

Revision ID: c1a5f7d9b2e4
Revises: 8f2b9c1d4e6a
Create Date: 2026-06-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1a5f7d9b2e4"
down_revision: Union[str, Sequence[str], None] = "8f2b9c1d4e6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_handoff_verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("pickup_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("dropoff_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("pickup_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("dropoff_attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_handoff_verifications_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_handoff_verifications")),
    )
    op.create_index(
        op.f("ix_order_handoff_verifications_order_id"),
        "order_handoff_verifications",
        ["order_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_order_handoff_verifications_order_id"),
        table_name="order_handoff_verifications",
    )
    op.drop_table("order_handoff_verifications")
