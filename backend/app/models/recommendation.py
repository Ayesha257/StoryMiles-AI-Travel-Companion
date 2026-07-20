from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RecommendationStatus, pg_enum


class RecommendationHistory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendation_history"

    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    prompt: Mapped[str] = mapped_column(String(2000), nullable=False)
    recommendations: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(pg_enum(RecommendationStatus, name="recommendation_status"), default=RecommendationStatus.GENERATED, nullable=False)

    user: Mapped["User"] = relationship(back_populates="recommendations")


from app.models.user import User
