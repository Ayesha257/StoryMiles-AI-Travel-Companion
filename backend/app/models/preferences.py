from __future__ import annotations

from sqlalchemy import ARRAY, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import BudgetLevel, TravelStyle, pg_enum


class UserPreferences(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    travel_styles: Mapped[list[TravelStyle]] = mapped_column(ARRAY(pg_enum(TravelStyle, name="travel_style")), default=list, nullable=False)
    budget_level: Mapped[BudgetLevel] = mapped_column(pg_enum(BudgetLevel, name="budget_level"), default=BudgetLevel.MEDIUM, nullable=False)
    preferred_currencies: Mapped[list[str]] = mapped_column(ARRAY(String(3)), default=lambda: ["USD"], nullable=False)
    preferred_languages: Mapped[list[str]] = mapped_column(ARRAY(String(10)), default=lambda: ["en"], nullable=False)
    dietary_requirements: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list, nullable=False)
    accessibility_needs: Mapped[list[str]] = mapped_column(ARRAY(String(100)), default=list, nullable=False)
    min_trip_days: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    max_trip_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    extra_preferences: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    marketing_emails: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="preferences")


from app.models.user import User
