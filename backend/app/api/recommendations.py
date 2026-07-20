from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_history_service, get_recommendation_engine
from app.auth.dependencies import CurrentUser
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.repositories.preferences import PreferencesRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.history import HistoryService
from app.services.recommendation import RecommendationEngine

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/generate", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    current_user: CurrentUser,
    engine: Annotated[RecommendationEngine, Depends(get_recommendation_engine)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationResponse:
    preferences = await PreferencesRepository(db).get_for_user(current_user.id)
    result = await engine.recommend(current_user.id, request, preferences)
    await db.commit()
    return result


@router.get("/history", response_model=list[RecommendationResponse])
async def list_history(
    current_user: CurrentUser,
    service: Annotated[HistoryService, Depends(get_history_service)],
    offset: int = 0,
    limit: int = 100,
) -> object:
    return await service.list_recommendations(current_user.id, offset=max(offset, 0), limit=min(max(limit, 1), 100))


@router.get("/history/{history_id}", response_model=RecommendationResponse)
async def get_history_item(
    history_id: UUID,
    current_user: CurrentUser,
    service: Annotated[HistoryService, Depends(get_history_service)],
) -> object:
    history = await service.get_recommendation(current_user.id, history_id)
    if history is None:
        raise NotFoundError("Recommendation history item not found")
    return history
