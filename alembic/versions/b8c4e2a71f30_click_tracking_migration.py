"""Add click metadata and a per-link count index.

Copy this file to itamityt-backend/alembic/versions before running Alembic.

Revision ID: b8c4e2a71f30
Revises: 9a84c5e2d761
Create Date: 2026-10-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c4e2a71f30"
down_revision: Union[str, Sequence[str], None] = "9a84c5e2d761"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("clicks", sa.Column("ip_address", sa.String(length=45), nullable=True))
    op.add_column("clicks", sa.Column("user_agent", sa.Text(), nullable=True))
    op.add_column(
        "clicks",
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_clicks_link_id", "clicks", ["link_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_clicks_link_id", table_name="clicks")
    op.drop_column("clicks", "clicked_at")
    op.drop_column("clicks", "user_agent")
    op.drop_column("clicks", "ip_address")
