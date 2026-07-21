import asyncio
import logging
from uuid import UUID

from app.core.logging import log_event
from app.ml.feature_engineering import BUDGET_MAP
from app.ml.model_loader import get_recommendation_artifacts
from app.ml.prediction import popular_destinations, predict_destinations
from app.models.enums import RecommendationStatus
from app.models.preferences import UserPreferences
from app.repositories.recommendation import RecommendationRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse

logger = logging.getLogger("storymiles.recommendations")


class RecommendationEngine:
    def __init__(self, repository: RecommendationRepository) -> None:
        self.repository = repository

    async def recommend(self, user_id: UUID, request: RecommendationRequest, preferences: UserPreferences | None) -> RecommendationResponse:
        preference_budget = preferences.budget_level.value if preferences else "medium"
        user_budget = request.budget_level or preference_budget
        # The supplied model was trained only on low, medium, and high tiers.
        # Existing legacy "luxury" preferences are represented by its high tier.
        if user_budget == "luxury":
            user_budget = "high"
        if user_budget not in BUDGET_MAP:
            raise ValueError("budget must be one of: low, medium, high")
        interests = request.interests or (
            [style.value for style in preferences.travel_styles]
            if preferences and preferences.travel_styles
            else [style.value for style in request.travel_styles or []]
        )

        used_fallback = False
        artifacts = get_recommendation_artifacts()
        try:
            predictions = await asyncio.to_thread(
                predict_destinations,
                artifacts=artifacts,
                user_budget=user_budget,
                user_weather_preference=request.weather_preference,
                user_interests=interests,
                user_trip_duration=request.trip_days,
                top_n=request.top_n,
            )
        except Exception as exc:
            # Local sklearn model — not a paid API, but still can fail if inference
            # blows up. Fall back to popular destinations so the page never goes blank.
            used_fallback = True
            log_event(
                logger,
                logging.ERROR,
                "Recommendation model failed — using popular destinations fallback",
                event="ml_fallback",
                endpoint="POST /recommendations/generate",
                user_id=str(user_id),
                error_type=type(exc).__name__,
                recovered=True,
                exc_info=True,
            )
            try:
                predictions = await asyncio.to_thread(
                    popular_destinations,
                    artifacts=artifacts,
                    top_n=request.top_n,
                )
            except Exception as fallback_exc:
                log_event(
                    logger,
                    logging.ERROR,
                    "Popular destinations fallback also failed",
                    event="ml_fallback_failed",
                    endpoint="POST /recommendations/generate",
                    user_id=str(user_id),
                    error_type=type(fallback_exc).__name__,
                    recovered=False,
                    exc_info=True,
                )
                raise

        recommendations = [
            {
                "name": prediction.name,
                "country": prediction.country,
                "city": prediction.name,
                "description": prediction.explanation,
                "reasons": [prediction.explanation],
                "best_time_to_visit": f"Best weather: {prediction.best_weather}",
                "estimated_daily_budget": prediction.budget_tier,
                "highlights": prediction.tags,
                "predicted_score": prediction.predicted_score,
                "explanation": prediction.explanation,
            }
            for prediction in predictions
        ]
        model_name = (
            f"popular_fallback:{type(artifacts.model).__name__}"
            if used_fallback
            else type(artifacts.model).__name__
        )
        history = await self.repository.create(
            user_id=user_id,
            prompt=request.prompt,
            recommendations=recommendations,
            model=model_name,
            status=RecommendationStatus.GENERATED,
        )
        return RecommendationResponse.model_validate(history)
