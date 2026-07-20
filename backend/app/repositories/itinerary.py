from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.itinerary import Itinerary
from app.repositories.base import BaseRepository


class ItineraryRepository(BaseRepository[Itinerary]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Itinerary)

    async def get_for_user(self, itinerary_id: UUID, user_id: UUID) -> Itinerary | None:
        return await self.session.scalar(select(Itinerary).where(Itinerary.id == itinerary_id, Itinerary.user_id == user_id))

    async def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[Itinerary]:
        statement = select(Itinerary).where(Itinerary.user_id == user_id).order_by(Itinerary.created_at.desc()).offset(offset).limit(limit)
        return (await self.session.scalars(statement)).all()
