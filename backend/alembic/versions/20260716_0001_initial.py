"""initial schema

Revision ID: 20260716_0001
Revises:
Create Date: 2026-07-16 00:00:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260716_0001"
down_revision = None
branch_labels = None
depends_on = None


travel_style = postgresql.ENUM(
    "adventure", "cultural", "food", "luxury", "nature", "relaxation", "budget", "family",
    name="travel_style", create_type=False,
)
budget_level = postgresql.ENUM("low", "medium", "high", "luxury", name="budget_level", create_type=False)
trip_status = postgresql.ENUM("draft", "planned", "completed", "archived", name="trip_status", create_type=False)
image_purpose = postgresql.ENUM("profile", "landmark_scan", "itinerary", name="image_purpose", create_type=False)
recommendation_status = postgresql.ENUM("generated", "saved", "dismissed", name="recommendation_status", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for enum in (travel_style, budget_level, trip_status, image_purpose, recommendation_status):
        enum.create(bind, checkfirst=True)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("first_name", sa.String(100)), sa.Column("last_name", sa.String(100)), sa.Column("bio", sa.Text()),
        sa.Column("date_of_birth", sa.Date()), sa.Column("avatar_url", sa.String(2048)), sa.Column("country", sa.String(100)), sa.Column("city", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "user_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("travel_styles", postgresql.ARRAY(travel_style), nullable=False, server_default="{}"), sa.Column("budget_level", budget_level, nullable=False, server_default="medium"),
        sa.Column("preferred_currencies", postgresql.ARRAY(sa.String(3)), nullable=False, server_default="{USD}"), sa.Column("preferred_languages", postgresql.ARRAY(sa.String(10)), nullable=False, server_default="{en}"),
        sa.Column("dietary_requirements", postgresql.ARRAY(sa.String(100)), nullable=False, server_default="{}"), sa.Column("accessibility_needs", postgresql.ARRAY(sa.String(100)), nullable=False, server_default="{}"),
        sa.Column("min_trip_days", sa.Integer(), nullable=False, server_default="2"), sa.Column("max_trip_days", sa.Integer(), nullable=False, server_default="7"), sa.Column("extra_preferences", postgresql.JSONB(), nullable=False, server_default="{}"), sa.Column("marketing_emails", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id"),
    )
    op.create_table(
        "destinations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("country", sa.String(100), nullable=False), sa.Column("city", sa.String(100)), sa.Column("description", sa.Text()),
        sa.Column("latitude", sa.Float()), sa.Column("longitude", sa.Float()), sa.Column("cover_image_url", sa.String(2048)), sa.Column("tags", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("is_visited", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_destinations_user_id", "destinations", ["user_id"])
    op.create_table(
        "recommendation_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prompt", sa.String(2000), nullable=False), sa.Column("recommendations", postgresql.JSONB(), nullable=False), sa.Column("model", sa.String(100), nullable=False), sa.Column("status", recommendation_status, nullable=False, server_default="generated"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recommendation_history_user_id", "recommendation_history", ["user_id"])
    op.create_table(
        "itineraries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("destination_id", postgresql.UUID(as_uuid=True)),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("summary", sa.Text()), sa.Column("start_date", sa.Date()), sa.Column("end_date", sa.Date()), sa.Column("travelers_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", trip_status, nullable=False, server_default="draft"), sa.Column("generated_by_model", sa.String(100)), sa.Column("itinerary_data", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["destination_id"], ["destinations.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_itineraries_user_id", "itineraries", ["user_id"])
    op.create_table(
        "image_uploads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False), sa.Column("storage_key", sa.String(1024), nullable=False), sa.Column("content_type", sa.String(100), nullable=False), sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("purpose", image_purpose, nullable=False), sa.Column("public_url", sa.String(2048), nullable=False), sa.Column("recognition_result", postgresql.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_image_uploads_user_id", "image_uploads", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_image_uploads_user_id", table_name="image_uploads")
    op.drop_table("image_uploads")
    op.drop_index("ix_itineraries_user_id", table_name="itineraries")
    op.drop_table("itineraries")
    op.drop_index("ix_recommendation_history_user_id", table_name="recommendation_history")
    op.drop_table("recommendation_history")
    op.drop_index("ix_destinations_user_id", table_name="destinations")
    op.drop_table("destinations")
    op.drop_table("user_preferences")
    op.drop_table("user_profiles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    bind = op.get_bind()
    for enum in (recommendation_status, image_purpose, trip_status, budget_level, travel_style):
        enum.drop(bind, checkfirst=True)
