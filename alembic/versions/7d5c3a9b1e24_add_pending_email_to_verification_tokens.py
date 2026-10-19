"""Add pending email to verification tokens.

Revision ID: 7d5c3a9b1e24
Revises: 41c64d6122a5
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d5c3a9b1e24"
down_revision: Union[str, Sequence[str], None] = "41c64d6122a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_verification_tokens",
        sa.Column("pending_email", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("email_verification_tokens", "pending_email")
