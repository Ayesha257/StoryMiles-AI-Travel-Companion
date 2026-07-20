"""Rank all supplied destinations using the pre-trained recommender."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.ml.feature_engineering import build_feature_frame, normalise_user_interests
from app.ml.model_loader import RecommendationArtifacts


@dataclass(frozen=True)
class PredictedDestination:
    name: str
    country: str
    budget_tier: str
    best_weather: str
    tags: list[str]
    ideal_duration: int
    predicted_score: float
    explanation: str


def _tags(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def predict_destinations(
    *,
    artifacts: RecommendationArtifacts,
    user_budget: str,
    user_weather_preference: str,
    user_interests: Iterable[object] | None,
    user_trip_duration: int,
    top_n: int,
) -> list[PredictedDestination]:
    """Score every CSV destination with the trained model and return top ``N``."""
    if top_n < 1:
        raise ValueError("top_n must be at least 1")

    features = build_feature_frame(
        destinations=artifacts.destinations,
        feature_columns=artifacts.feature_columns,
        user_budget=user_budget,
        user_weather_preference=user_weather_preference,
        user_interests=user_interests,
        user_trip_duration=user_trip_duration,
    )
    scores = artifacts.model.predict(features)
    ranked_indexes = sorted(range(len(scores)), key=lambda index: float(scores[index]), reverse=True)[:top_n]
    interest_set = normalise_user_interests(user_interests)
    results: list[PredictedDestination] = []

    for index in ranked_indexes:
        destination = artifacts.destinations.iloc[index]
        tags = _tags(destination["tags"])
        overlap = len(interest_set & {tag.lower() for tag in tags})
        duration_difference = abs(user_trip_duration - int(destination["ideal_duration"]))
        score = float(scores[index])
        explanation = (
            f"Predicted match score {score:.2f}: {destination['name']} has a {destination['budget_tier']} budget tier, "
            f"{overlap} shared interest tag(s), and a {duration_difference}-day duration difference."
        )
        results.append(
            PredictedDestination(
                name=str(destination["name"]),
                country=str(destination["country"]),
                budget_tier=str(destination["budget_tier"]),
                best_weather=str(destination["best_weather"]),
                tags=tags,
                ideal_duration=int(destination["ideal_duration"]),
                predicted_score=score,
                explanation=explanation,
            )
        )
    return results
