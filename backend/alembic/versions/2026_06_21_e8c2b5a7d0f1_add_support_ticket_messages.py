"""add support ticket messages

Revision ID: e8c2b5a7d0f1
Revises: d4b7e3a91f2c
Create Date: 2026-06-21 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8c2b5a7d0f1"
down_revision: Union[str, Sequence[str], None] = "d4b7e3a91f2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "support_ticket_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ticket_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_internal", sa.Boolean(), server_default="false", nullable=False),
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
            ["author_id"],
            ["users.id"],
            name=op.f("fk_support_ticket_messages_author_id_users"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["ticket_id"],
            ["support_tickets.id"],
            name=op.f("fk_support_ticket_messages_ticket_id_support_tickets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_support_ticket_messages")),
    )
    op.create_index(
        op.f("ix_support_ticket_messages_author_id"),
        "support_ticket_messages",
        ["author_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_support_ticket_messages_ticket_id"),
        "support_ticket_messages",
        ["ticket_id"],
        unique=False,
    )
    op.create_index(
        "ix_support_ticket_messages_ticket_created",
        "support_ticket_messages",
        ["ticket_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_support_ticket_messages_ticket_created",
        table_name="support_ticket_messages",
    )
    op.drop_index(
        op.f("ix_support_ticket_messages_ticket_id"),
        table_name="support_ticket_messages",
    )
    op.drop_index(
        op.f("ix_support_ticket_messages_author_id"),
        table_name="support_ticket_messages",
    )
    op.drop_table("support_ticket_messages")
