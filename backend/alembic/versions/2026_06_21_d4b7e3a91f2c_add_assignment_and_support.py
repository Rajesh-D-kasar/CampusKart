"""add assignment and support

Revision ID: d4b7e3a91f2c
Revises: c1a5f7d9b2e4
Create Date: 2026-06-21 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4b7e3a91f2c"
down_revision: Union[str, Sequence[str], None] = "c1a5f7d9b2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column("assigned_delivery_partner_id", sa.Integer(), nullable=True),
        )
        batch_op.create_index(
            op.f("ix_orders_assigned_delivery_partner_id"),
            ["assigned_delivery_partner_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            op.f("fk_orders_assigned_delivery_partner_id_users"),
            "users",
            ["assigned_delivery_partner_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.add_column(
        "order_handoff_verifications",
        sa.Column("store_ready_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "support_tickets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("requester_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("audience", sa.String(length=30), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=140), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="open", nullable=False),
        sa.Column(
            "priority",
            sa.String(length=30),
            server_default="normal",
            nullable=False,
        ),
        sa.Column("resolution", sa.Text(), nullable=True),
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
            name=op.f("fk_support_tickets_order_id_orders"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"],
            ["users.id"],
            name=op.f("fk_support_tickets_requester_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_support_tickets")),
    )
    op.create_index(
        op.f("ix_support_tickets_audience"),
        "support_tickets",
        ["audience"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_tickets_category"),
        "support_tickets",
        ["category"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_requester_created",
        "support_tickets",
        ["requester_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_support_tickets_status_created",
        "support_tickets",
        ["status", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_tickets_order_id"),
        "support_tickets",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_tickets_requester_id"),
        "support_tickets",
        ["requester_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_tickets_status"),
        "support_tickets",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_support_tickets_status"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_requester_id"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_order_id"), table_name="support_tickets")
    op.drop_index("ix_support_tickets_status_created", table_name="support_tickets")
    op.drop_index("ix_support_tickets_requester_created", table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_category"), table_name="support_tickets")
    op.drop_index(op.f("ix_support_tickets_audience"), table_name="support_tickets")
    op.drop_table("support_tickets")
    op.drop_column("order_handoff_verifications", "store_ready_at")
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_orders_assigned_delivery_partner_id_users"),
            type_="foreignkey",
        )
        batch_op.drop_index(op.f("ix_orders_assigned_delivery_partner_id"))
        batch_op.drop_column("assigned_delivery_partner_id")
