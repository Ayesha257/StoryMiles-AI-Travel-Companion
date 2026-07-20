from uuid import UUID

from pydantic import Field

from app.schemas.common import Schema, TimestampedSchema


class DestinationCreate(Schema):
    name: str = Field(min_length=1, max_length=200)
    country: str = Field(min_length=1, max_length=100)
    city: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    cover_image_url: str | None = Field(default=None, max_length=2048)
    tags: list[str] = Field(default_factory=list, max_length=25)
    is_favorite: bool = False
    is_visited: bool = False


class DestinationUpdate(DestinationCreate):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = Field(default=None, min_length=1, max_length=100)


class DestinationResponse(TimestampedSchema):
    user_id: UUID
    name: str
    country: str
    city: str | None
    description: str | None
    latitude: float | None
    longitude: float | None
    cover_image_url: str | None
    tags: list[str]
    is_favorite: bool
    is_visited: bool
