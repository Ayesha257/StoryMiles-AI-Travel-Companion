"""add verification code purpose for password resets

Revision ID: 20260719_0004
Revises: 20260719_0003
Create Date: 2026-07-19 11:58:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260719_0004"
down_revision = "20260719_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verification_code_purpose", sa.String(32)))
    op.execute(
        "UPDATE users SET verification_code_purpose = 'email_verification' "
        "WHERE verification_code_hash IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column("users", "verification_code_purpose")
