from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.album import AlbumPhoto, TripAlbum
from app.repositories.base import BaseRepository


class AlbumRepository(BaseRepository[TripAlbum]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TripAlbum)

    async def get_for_user(self, album_id: UUID, user_id: UUID) -> TripAlbum | None:
        statement = (
            select(TripAlbum)
            .options(selectinload(TripAlbum.photos).selectinload(AlbumPhoto.image))
            .where(TripAlbum.id == album_id, TripAlbum.user_id == user_id)
            .execution_options(populate_existing=True)
        )
        return await self.session.scalar(statement)

    async def list_for_user(self, user_id: UUID) -> Sequence[TripAlbum]:
        statement = (
            select(TripAlbum)
            .options(selectinload(TripAlbum.photos).selectinload(AlbumPhoto.image))
            .where(TripAlbum.user_id == user_id)
            .order_by(TripAlbum.created_at.desc())
        )
        return (await self.session.scalars(statement)).unique().all()

    async def add_photo(self, album_id: UUID, image_id: UUID) -> AlbumPhoto:
        position = await self.session.scalar(
            select(func.count()).select_from(AlbumPhoto).where(AlbumPhoto.album_id == album_id)
        )
        photo = AlbumPhoto(album_id=album_id, image_id=image_id, position=position or 0)
        self.session.add(photo)
        await self.session.flush()
        return photo

    async def count_photos(self, album_id: UUID) -> int:
        total = await self.session.scalar(
            select(func.count()).select_from(AlbumPhoto).where(AlbumPhoto.album_id == album_id)
        )
        return int(total or 0)
