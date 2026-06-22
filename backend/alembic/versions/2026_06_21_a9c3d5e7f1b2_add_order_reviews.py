"""add order reviews

Revision ID: a9c3d5e7f1b2
Revises: f2b7c4d8a913
Create Date: 2026-06-21 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a9c3d5e7f1b2"
down_revision: Union[str, Sequence[str], None] = "f2b7c4d8a913"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "order_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=True),
        sa.Column("delivery_partner_id", sa.Integer(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=False),
        sa.Column("product_rating", sa.Integer(), nullable=False),
        sa.Column("delivery_rating", sa.Integer(), nullable=False),
        sa.Column("seller_rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(length=500), nullable=True),
        sa.Column("issue_tags", sa.JSON(), nullable=True),
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
        sa.CheckConstraint(
            "overall_rating >= 1 AND overall_rating <= 5",
            name=op.f("ck_order_reviews_overall_rating_range"),
        ),
        sa.CheckConstraint(
            "product_rating >= 1 AND product_rating <= 5",
            name=op.f("ck_order_reviews_product_rating_range"),
        ),
        sa.CheckConstraint(
            "delivery_rating >= 1 AND delivery_rating <= 5",
            name=op.f("ck_order_reviews_delivery_rating_range"),
        ),
        sa.CheckConstraint(
            "seller_rating >= 1 AND seller_rating <= 5",
            name=op.f("ck_order_reviews_seller_rating_range"),
        ),
        sa.ForeignKeyConstraint(
            ["delivery_partner_id"],
            ["users.id"],
            name=op.f("fk_order_reviews_delivery_partner_id_users"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["order_id"],
            ["orders.id"],
            name=op.f("fk_order_reviews_order_id_orders"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["store_id"],
            ["stores.id"],
            name=op.f("fk_order_reviews_store_id_stores"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_order_reviews_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_order_reviews")),
        sa.UniqueConstraint("order_id", name="uq_order_reviews_order_id"),
    )
    op.create_index(op.f("ix_order_reviews_order_id"), "order_reviews", ["order_id"], unique=False)
    op.create_index(op.f("ix_order_reviews_user_id"), "order_reviews", ["user_id"], unique=False)
    op.create_index(op.f("ix_order_reviews_store_id"), "order_reviews", ["store_id"], unique=False)
    op.create_index(
        op.f("ix_order_reviews_delivery_partner_id"),
        "order_reviews",
        ["delivery_partner_id"],
        unique=False,
    )
    op.create_index(
        "ix_order_reviews_user_created",
        "order_reviews",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_order_reviews_store_created",
        "order_reviews",
        ["store_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_order_reviews_partner_created",
        "order_reviews",
        ["delivery_partner_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_reviews_partner_created", table_name="order_reviews")
    op.drop_index("ix_order_reviews_store_created", table_name="order_reviews")
    op.drop_index("ix_order_reviews_user_created", table_name="order_reviews")
    op.drop_index(op.f("ix_order_reviews_delivery_partner_id"), table_name="order_reviews")
    op.drop_index(op.f("ix_order_reviews_store_id"), table_name="order_reviews")
    op.drop_index(op.f("ix_order_reviews_user_id"), table_name="order_reviews")
    op.drop_index(op.f("ix_order_reviews_order_id"), table_name="order_reviews")
    op.drop_table("order_reviews")
