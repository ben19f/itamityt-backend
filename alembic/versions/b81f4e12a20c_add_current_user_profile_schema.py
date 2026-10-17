"""Add profile and verification schema required by the current API.

Revision ID: b81f4e12a20c
Revises: 03421efc787e
Create Date: 2026-10-18
"""
from typing import Sequence, Union

from alembic import op


revision: str = "b81f4e12a20c"
down_revision: Union[str, Sequence[str], None] = "03421efc787e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF NOT EXISTS also makes this safe for databases where some fields were
    # added manually before the migration was introduced.
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN")
    op.execute(
        "UPDATE users SET email_verified = TRUE WHERE email_verified IS NULL"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN email_verified SET DEFAULT FALSE"
    )
    op.execute(
        "ALTER TABLE users ALTER COLUMN email_verified SET NOT NULL"
    )

    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_description TEXT"
    )
    op.execute(
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_extra_info TEXT"
    )
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS owner_verified VARCHAR(1)")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS service_verified VARCHAR(1)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS user_photos (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            image_url VARCHAR NOT NULL,
            position INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_user_photos_user_id ON user_photos (user_id)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS email_verification_tokens (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            token_hash VARCHAR NOT NULL UNIQUE,
            expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_email_verification_tokens_user_id "
        "ON email_verification_tokens (user_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_email_verification_tokens_token_hash "
        "ON email_verification_tokens (token_hash)"
    )


def downgrade() -> None:
    op.drop_table("email_verification_tokens")
    op.drop_table("user_photos")
    op.drop_column("users", "service_verified")
    op.drop_column("users", "owner_verified")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "profile_extra_info")
    op.drop_column("users", "profile_description")
    op.drop_column("users", "display_name")
    op.drop_column("users", "email_verified")
