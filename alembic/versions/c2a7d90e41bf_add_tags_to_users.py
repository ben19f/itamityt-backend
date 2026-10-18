"""Add tags dictionary to user profiles.

Revision ID: c2a7d90e41bf
Revises: b81f4e12a20c
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op


revision: str = "c2a7d90e41bf"
down_revision: Union[str, Sequence[str], None] = "b81f4e12a20c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS tags JSONB "
        "NOT NULL DEFAULT '{}'::jsonb"
    )


def downgrade() -> None:
    op.drop_column("users", "tags")
