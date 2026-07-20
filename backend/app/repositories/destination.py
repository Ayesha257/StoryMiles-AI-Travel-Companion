from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.destination import Destination
from app.repositories.base import BaseRepository


class DestinationRepository(BaseRepository[Destination]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Destination)

    async def get_for_user(self, destination_id: UUID, user_id: UUID) -> Destination | None:
        return await self.session.scalar(select(Destination).where(Destination.id == destination_id, Destination.user_id == user_id))

    async def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[Destination]:
        statement = select(Destination).where(Destination.user_id == user_id).order_by(Destination.created_at.desc()).offset(offset).limit(limit)
        return (await self.session.scalars(statement)).all()
