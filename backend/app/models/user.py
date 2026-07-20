from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    profile: Mapped[UserProfile | None] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    preferences: Mapped[UserPreferences | None] = relationship(back_populates="user", cascade="all, delete-orphan", uselist=False)
    destinations: Mapped[list[Destination]] = relationship(back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list[RecommendationHistory]] = relationship(back_populates="user", cascade="all, delete-orphan")
    itineraries: Mapped[list[Itinerary]] = relationship(back_populates="user", cascade="all, delete-orphan")
    uploads: Mapped[list[ImageUpload]] = relationship(back_populates="user", cascade="all, delete-orphan")
    albums: Mapped[list[TripAlbum]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
    bio: Mapped[str | None] = mapped_column(Text)
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    avatar_url: Mapped[str | None] = mapped_column(String(2048))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))

    user: Mapped[User] = relationship(back_populates="profile")


from app.models.album import TripAlbum
from app.models.destination import Destination
from app.models.image import ImageUpload
from app.models.itinerary import Itinerary
from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationHistory
