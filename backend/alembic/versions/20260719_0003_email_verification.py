"""add email verification codes

Revision ID: 20260719_0003
Revises: 20260719_0002
Create Date: 2026-07-19 11:30:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260719_0003"
down_revision = "20260719_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verification_code_hash", sa.String(64)))
    op.add_column("users", sa.Column("verification_code_expires_at", sa.DateTime(timezone=True)))
    op.add_column("users", sa.Column("verification_code_sent_at", sa.DateTime(timezone=True)))
    op.add_column(
        "users",
        sa.Column("verification_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    # Existing accounts predate email verification and must remain usable.
    op.execute("UPDATE users SET is_verified = true")


def downgrade() -> None:
    op.drop_column("users", "verification_attempts")
    op.drop_column("users", "verification_code_sent_at")
    op.drop_column("users", "verification_code_expires_at")
    op.drop_column("users", "verification_code_hash")
