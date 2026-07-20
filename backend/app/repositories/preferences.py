from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preferences import UserPreferences
from app.repositories.base import BaseRepository


class PreferencesRepository(BaseRepository[UserPreferences]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserPreferences)

    async def get_for_user(self, user_id: UUID) -> UserPreferences | None:
        return await self.session.scalar(select(UserPreferences).where(UserPreferences.user_id == user_id))
