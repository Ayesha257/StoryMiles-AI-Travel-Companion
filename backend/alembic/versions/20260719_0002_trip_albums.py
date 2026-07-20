"""add trip photo albums

Revision ID: 20260719_0002
Revises: 20260716_0001
Create Date: 2026-07-19 03:40:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260719_0002"
down_revision = "20260716_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE image_purpose ADD VALUE IF NOT EXISTS 'album'")
    op.create_table(
        "trip_albums",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("destination", sa.String(200)),
        sa.Column("description", sa.Text()),
        sa.Column("trip_start", sa.Date()),
        sa.Column("trip_end", sa.Date()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_trip_albums_user_id", "trip_albums", ["user_id"])
    op.create_table(
        "album_photos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("album_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("image_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("caption", sa.String(500)),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["album_id"], ["trip_albums.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["image_id"], ["image_uploads.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("album_id", "image_id"),
    )
    op.create_index("ix_album_photos_album_id", "album_photos", ["album_id"])


def downgrade() -> None:
    op.drop_index("ix_album_photos_album_id", table_name="album_photos")
    op.drop_table("album_photos")
    op.drop_index("ix_trip_albums_user_id", table_name="trip_albums")
    op.drop_table("trip_albums")
    # PostgreSQL enum values cannot be removed safely without recreating the type.
