"""Add purpose to verification tokens.

Revision ID: 9a84c5e2d761
Revises: 7d5c3a9b1e24
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9a84c5e2d761"
down_revision: Union[str, Sequence[str], None] = "7d5c3a9b1e24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "email_verification_tokens",
        sa.Column(
            "purpose",
            sa.String(),
            nullable=False,
            server_default="email_verification",
        ),
    )


def downgrade() -> None:
    op.drop_column("email_verification_tokens", "purpose")
