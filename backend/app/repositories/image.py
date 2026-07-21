from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import ImageUpload
from app.repositories.base import BaseRepository


class ImageRepository(BaseRepository[ImageUpload]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ImageUpload)

    async def get_for_user(self, image_id: UUID, user_id: UUID) -> ImageUpload | None:
        return await self.session.scalar(select(ImageUpload).where(ImageUpload.id == image_id, ImageUpload.user_id == user_id))

    async def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[ImageUpload]:
        statement = select(ImageUpload).where(ImageUpload.user_id == user_id).order_by(ImageUpload.created_at.desc()).offset(offset).limit(limit)
        return (await self.session.scalars(statement)).all()

    async def total_size_bytes_for_user(self, user_id: UUID) -> int:
        total = await self.session.scalar(
            select(func.coalesce(func.sum(ImageUpload.size_bytes), 0)).where(ImageUpload.user_id == user_id)
        )
        return int(total or 0)
