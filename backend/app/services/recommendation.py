import asyncio
from uuid import UUID

from app.models.enums import RecommendationStatus
from app.models.preferences import UserPreferences
from app.ml.feature_engineering import BUDGET_MAP
from app.ml.model_loader import get_recommendation_artifacts
from app.ml.prediction import predict_destinations
from app.repositories.recommendation import RecommendationRepository
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse


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
        predictions = await asyncio.to_thread(
            predict_destinations,
            artifacts=get_recommendation_artifacts(),
            user_budget=user_budget,
            user_weather_preference=request.weather_preference,
            user_interests=interests,
            user_trip_duration=request.trip_days,
            top_n=request.top_n,
        )
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
        history = await self.repository.create(
            user_id=user_id,
            prompt=request.prompt,
            recommendations=recommendations,
            model=type(get_recommendation_artifacts().model).__name__,
            status=RecommendationStatus.GENERATED,
        )
        return RecommendationResponse.model_validate(history)
