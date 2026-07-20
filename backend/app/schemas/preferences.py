from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import BudgetLevel, TravelStyle
from app.schemas.common import Schema, TimestampedSchema


class PreferencesUpdate(Schema):
    travel_styles: list[TravelStyle] | None = None
    budget_level: BudgetLevel | None = None
    preferred_currencies: list[str] | None = Field(default=None, max_length=10)
    preferred_languages: list[str] | None = Field(default=None, max_length=10)
    dietary_requirements: list[str] | None = Field(default=None, max_length=20)
    accessibility_needs: list[str] | None = Field(default=None, max_length=20)
    min_trip_days: int | None = Field(default=None, ge=1, le=365)
    max_trip_days: int | None = Field(default=None, ge=1, le=365)
    extra_preferences: dict | None = None
    marketing_emails: bool | None = None

    @model_validator(mode="after")
    def validate_day_range(self) -> "PreferencesUpdate":
        if self.min_trip_days and self.max_trip_days and self.min_trip_days > self.max_trip_days:
            raise ValueError("min_trip_days cannot exceed max_trip_days")
        return self


class PreferencesResponse(TimestampedSchema):
    user_id: UUID
    travel_styles: list[TravelStyle]
    budget_level: BudgetLevel
    preferred_currencies: list[str]
    preferred_languages: list[str]
    dietary_requirements: list[str]
    accessibility_needs: list[str]
    min_trip_days: int
    max_trip_days: int
    extra_preferences: dict
    marketing_emails: bool
