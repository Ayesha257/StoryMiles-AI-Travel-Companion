from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import TripStatus, pg_enum


class Itinerary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "itineraries"

    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    destination_id: Mapped[object | None] = mapped_column(UUID(as_uuid=True), ForeignKey("destinations.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    travelers_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[TripStatus] = mapped_column(pg_enum(TripStatus, name="trip_status"), default=TripStatus.DRAFT, nullable=False)
    generated_by_model: Mapped[str | None] = mapped_column(String(100))
    itinerary_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    user: Mapped["User"] = relationship(back_populates="itineraries")
    destination: Mapped["Destination | None"] = relationship(back_populates="itineraries")


from app.models.destination import Destination
from app.models.user import User
