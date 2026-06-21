"""add payment notifications tracking

Revision ID: f2b7c4d8a913
Revises: e8c2b5a7d0f1
Create Date: 2026-06-21 00:00:03.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2b7c4d8a913"
down_revision: Union[str, Sequence[str], None] = "e8c2b5a7d0f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_items",
        sa.Column("packed_quantity", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "order_items",
        sa.Column(
            "fulfillment_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
    )
    op.add_column(
        "order_items",
        sa.Column("substitution_note", sa.String(length=255), nullable=True),
    )
    op.create_index(
        op.f("ix_order_items_fulfillment_status"),
        "order_items",
        ["fulfillment_status"],
        unique=False,
    )

    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("provider", sa.String(length=40), nullable=False),
        sa.Column("provider_order_id", sa.String(length=100), nullable=True),
        sa.Column("provider_payment_id", sa.String(length=100), nullable=True),
        sa.Column("provider_refund_id", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("amount_paise", sa.Integer(), server_default="0", nullable=False),
        sa.Column("currency", sa.String(length=3), server_default="INR", nullable=False),
        sa.Column("verified", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("signature", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
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
            name=op.f("fk_payment_transactions_order_id_orders"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_payment_transactions_user_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_transactions")),
    )
    op.create_index(
        op.f("ix_payment_transactions_event_type"),
        "payment_transactions",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_order_id"),
        "payment_transactions",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_transactions_order_created",
        "payment_transactions",
        ["order_id", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_provider_order_id"),
        "payment_transactions",
        ["provider_order_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_transactions_provider_order",
        "payment_transactions",
        ["provider", "provider_order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_provider_payment_id"),
        "payment_transactions",
        ["provider_payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_payment_transactions_provider_payment",
        "payment_transactions",
        ["provider", "provider_payment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_provider_refund_id"),
        "payment_transactions",
        ["provider_refund_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_status"),
        "payment_transactions",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_payment_transactions_user_id"),
        "payment_transactions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("channel", sa.String(length=30), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=140), nullable=False),
        sa.Column("message", sa.String(length=500), nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
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
            name=op.f("fk_notifications_order_id_orders"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_notifications_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(
        op.f("ix_notifications_event_type"),
        "notifications",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_order_id"),
        "notifications",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notifications_user_id"),
        "notifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_user_read_created",
        "notifications",
        ["user_id", "is_read", "created_at"],
        unique=False,
    )

    op.create_table(
        "delivery_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("delivery_partner_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column("accuracy_meters", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("battery_percent", sa.Integer(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False),
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
            ["delivery_partner_id"],
            ["users.id"],
            name=op.f("fk_delivery_locations_delivery_partner_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_delivery_locations_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delivery_locations")),
    )
    op.create_index(
        op.f("ix_delivery_locations_delivery_partner_id"),
        "delivery_locations",
        ["delivery_partner_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_delivery_locations_order_id"),
        "delivery_locations",
        ["order_id"],
        unique=False,
    )
    op.create_index(
        "ix_delivery_locations_order_created",
        "delivery_locations",
        ["order_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_delivery_locations_order_created",
        table_name="delivery_locations",
    )
    op.drop_index(
        op.f("ix_delivery_locations_order_id"),
        table_name="delivery_locations",
    )
    op.drop_index(
        op.f("ix_delivery_locations_delivery_partner_id"),
        table_name="delivery_locations",
    )
    op.drop_table("delivery_locations")

    op.drop_index(
        "ix_notifications_user_read_created",
        table_name="notifications",
    )
    op.drop_index(op.f("ix_notifications_user_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_order_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_event_type"), table_name="notifications")
    op.drop_table("notifications")

    op.drop_index(op.f("ix_payment_transactions_user_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_status"), table_name="payment_transactions")
    op.drop_index(
        op.f("ix_payment_transactions_provider_refund_id"),
        table_name="payment_transactions",
    )
    op.drop_index(
        "ix_payment_transactions_provider_payment",
        table_name="payment_transactions",
    )
    op.drop_index(
        op.f("ix_payment_transactions_provider_payment_id"),
        table_name="payment_transactions",
    )
    op.drop_index(
        "ix_payment_transactions_provider_order",
        table_name="payment_transactions",
    )
    op.drop_index(
        op.f("ix_payment_transactions_provider_order_id"),
        table_name="payment_transactions",
    )
    op.drop_index(
        "ix_payment_transactions_order_created",
        table_name="payment_transactions",
    )
    op.drop_index(op.f("ix_payment_transactions_order_id"), table_name="payment_transactions")
    op.drop_index(op.f("ix_payment_transactions_event_type"), table_name="payment_transactions")
    op.drop_table("payment_transactions")

    op.drop_index(op.f("ix_order_items_fulfillment_status"), table_name="order_items")
    op.drop_column("order_items", "substitution_note")
    op.drop_column("order_items", "fulfillment_status")
    op.drop_column("order_items", "packed_quantity")
