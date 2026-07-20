from collections.abc import Sequence
from uuid import UUID

from app.models.recommendation import RecommendationHistory
from app.repositories.recommendation import RecommendationRepository


class HistoryService:
    def __init__(self, repository: RecommendationRepository) -> None:
        self.repository = repository

    async def list_recommendations(self, user_id: UUID, *, offset: int = 0, limit: int = 100) -> Sequence[RecommendationHistory]:
        return await self.repository.list_for_user(user_id, offset=offset, limit=limit)

    async def get_recommendation(self, user_id: UUID, history_id: UUID) -> RecommendationHistory | None:
        return await self.repository.get_for_user(history_id, user_id)
