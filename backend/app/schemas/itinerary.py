from datetime import date
from uuid import UUID

from pydantic import Field, model_validator

from app.models.enums import BudgetLevel, TripStatus
from app.schemas.common import Schema, TimestampedSchema


class ItineraryGenerateRequest(Schema):
    destination: str = Field(min_length=2, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    days: int = Field(default=3, ge=1, le=30)
    travelers_count: int = Field(default=1, ge=1, le=20)
    budget_level: BudgetLevel | None = None
    interests: list[str] = Field(default_factory=list, max_length=20)
    additional_notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def validate_dates(self) -> "ItineraryGenerateRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class ItineraryCreate(Schema):
    destination_id: UUID | None = None
    title: str = Field(min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    travelers_count: int = Field(default=1, ge=1, le=20)
    status: TripStatus = TripStatus.DRAFT
    itinerary_data: dict


class ItineraryUpdate(Schema):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    summary: str | None = Field(default=None, max_length=5000)
    start_date: date | None = None
    end_date: date | None = None
    travelers_count: int | None = Field(default=None, ge=1, le=20)
    status: TripStatus | None = None
    itinerary_data: dict | None = None


class ItineraryResponse(TimestampedSchema):
    user_id: UUID
    destination_id: UUID | None
    title: str
    summary: str | None
    start_date: date | None
    end_date: date | None
    travelers_count: int
    status: TripStatus
    generated_by_model: str | None
    itinerary_data: dict
