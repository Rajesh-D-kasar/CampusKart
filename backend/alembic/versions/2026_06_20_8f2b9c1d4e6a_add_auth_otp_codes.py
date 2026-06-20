"""add auth otp codes

Revision ID: 8f2b9c1d4e6a
Revises: 6ecddac9707d
Create Date: 2026-06-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8f2b9c1d4e6a"
down_revision: Union[str, Sequence[str], None] = "6ecddac9707d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "auth_otp_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("code_hash", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resend_available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="5", nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_auth_otp_codes")),
    )
    op.create_index(
        op.f("ix_auth_otp_codes_email"),
        "auth_otp_codes",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f("ix_auth_otp_codes_expires_at"),
        "auth_otp_codes",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_otp_email_created",
        "auth_otp_codes",
        ["email", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_auth_otp_email_consumed",
        "auth_otp_codes",
        ["email", "consumed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_auth_otp_email_consumed", table_name="auth_otp_codes")
    op.drop_index("ix_auth_otp_email_created", table_name="auth_otp_codes")
    op.drop_index(op.f("ix_auth_otp_codes_expires_at"), table_name="auth_otp_codes")
    op.drop_index(op.f("ix_auth_otp_codes_email"), table_name="auth_otp_codes")
    op.drop_table("auth_otp_codes")
