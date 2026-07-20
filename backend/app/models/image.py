from __future__ import annotations

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ImagePurpose, pg_enum


class ImageUpload(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "image_uploads"

    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    purpose: Mapped[ImagePurpose] = mapped_column(pg_enum(ImagePurpose, name="image_purpose"), nullable=False)
    public_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    recognition_result: Mapped[dict | None] = mapped_column(JSONB)

    user: Mapped["User"] = relationship(back_populates="uploads")


from app.models.user import User
