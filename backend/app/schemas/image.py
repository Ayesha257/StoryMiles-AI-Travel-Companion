from uuid import UUID

from pydantic import Field

from app.models.enums import ImagePurpose
from app.schemas.common import TimestampedSchema


class ImageUploadResponse(TimestampedSchema):
    user_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    purpose: ImagePurpose
    public_url: str
    recognition_result: dict | None


class LandmarkRecognitionResponse(ImageUploadResponse):
    landmark_name: str | None = None
    location: str | None = None
    country: str | None = None
    confidence: float | None = None
    description: str | None = None
    historical_background: str | None = None
    historical_facts: list[str] = Field(default_factory=list)
    architecture_style: str | None = None
    built_year: str | None = None
    why_it_matters: str | None = None
    visitor_tips: list[str] = Field(default_factory=list)
    best_time_to_visit: str | None = None
    nearby_highlights: list[str] = Field(default_factory=list)

    @classmethod
    def from_upload(cls, image: object) -> "LandmarkRecognitionResponse":
        """Flatten recognition_result JSONB into top-level response fields."""
        result = getattr(image, "recognition_result", None) or {}
        base = ImageUploadResponse.model_validate(image).model_dump()
        return cls(
            **base,
            landmark_name=result.get("landmark_name"),
            location=result.get("location"),
            country=result.get("country"),
            confidence=result.get("confidence"),
            description=result.get("description"),
            historical_background=result.get("historical_background"),
            historical_facts=result.get("historical_facts") or [],
            architecture_style=result.get("architecture_style"),
            built_year=result.get("built_year"),
            why_it_matters=result.get("why_it_matters"),
            visitor_tips=result.get("visitor_tips") or [],
            best_time_to_visit=result.get("best_time_to_visit"),
            nearby_highlights=result.get("nearby_highlights") or [],
        )
