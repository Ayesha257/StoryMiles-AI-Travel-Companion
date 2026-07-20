from typing import Literal
from uuid import UUID

from pydantic import Field

from app.models.enums import RecommendationStatus, TravelStyle
from app.schemas.common import Schema, TimestampedSchema


class RecommendationRequest(Schema):
    prompt: str = Field(min_length=3, max_length=2000)
    trip_days: int = Field(default=5, ge=1, le=30)
    budget_level: Literal["low", "medium", "high"] | None = None
    weather_preference: Literal["hot", "mild", "cold"] = "mild"
    interests: list[str] = Field(default_factory=list, max_length=20)
    travel_styles: list[TravelStyle] | None = None
    departure_city: str | None = Field(default=None, max_length=100)
    top_n: int = Field(default=5, ge=1, le=20)


class RecommendedDestination(Schema):
    name: str
    country: str
    city: str | None = None
    description: str
    reasons: list[str]
    best_time_to_visit: str
    estimated_daily_budget: str
    highlights: list[str]
    predicted_score: float
    explanation: str


class RecommendationResponse(TimestampedSchema):
    user_id: UUID
    prompt: str
    recommendations: list[RecommendedDestination]
    model: str
    status: RecommendationStatus
