from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserProfile
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower()).options(
            selectinload(User.profile), selectinload(User.preferences)
        )
        return await self.session.scalar(statement)

    async def get_with_relations(self, user_id: UUID) -> User | None:
        statement = select(User).where(User.id == user_id).options(
            selectinload(User.profile), selectinload(User.preferences)
        )
        return await self.session.scalar(statement)

    async def create_profile(self, user_id: UUID, **values: object) -> UserProfile:
        profile = UserProfile(user_id=user_id, **values)
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile
