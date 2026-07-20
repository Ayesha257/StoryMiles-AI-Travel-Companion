from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin


class TripAlbum(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "trip_albums"

    user_id: Mapped[object] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    trip_start: Mapped[date | None] = mapped_column(Date)
    trip_end: Mapped[date | None] = mapped_column(Date)

    user: Mapped["User"] = relationship(back_populates="albums")
    photos: Mapped[list["AlbumPhoto"]] = relationship(
        back_populates="album",
        cascade="all, delete-orphan",
        order_by="AlbumPhoto.position",
        lazy="selectin",
    )


class AlbumPhoto(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "album_photos"
    __table_args__ = (UniqueConstraint("album_id", "image_id"),)

    album_id: Mapped[object] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trip_albums.id", ondelete="CASCADE"), index=True, nullable=False
    )
    image_id: Mapped[object] = mapped_column(
        UUID(as_uuid=True), ForeignKey("image_uploads.id", ondelete="CASCADE"), nullable=False
    )
    caption: Mapped[str | None] = mapped_column(String(500))
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    album: Mapped[TripAlbum] = relationship(back_populates="photos")
    image: Mapped["ImageUpload"] = relationship(lazy="joined")


from app.models.image import ImageUpload
from app.models.user import User
