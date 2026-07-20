from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.recommendation import RecommendationHistory
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[RecommendationHistory]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RecommendationHistory)

    async def list_for_user(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[RecommendationHistory]:
        statement = (
            select(RecommendationHistory)
            .where(RecommendationHistory.user_id == user_id)
            .order_by(RecommendationHistory.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return (await self.session.scalars(statement)).all()

    async def get_for_user(self, history_id: UUID, user_id: UUID) -> RecommendationHistory | None:
        return await self.session.scalar(
            select(RecommendationHistory).where(RecommendationHistory.id == history_id, RecommendationHistory.user_id == user_id)
        )
