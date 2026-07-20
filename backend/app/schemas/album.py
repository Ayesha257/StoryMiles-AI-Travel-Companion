from datetime import date
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.common import Schema, TimestampedSchema


class AlbumCreate(Schema):
    title: str = Field(min_length=1, max_length=200)
    destination: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=3000)
    trip_start: date | None = None
    trip_end: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "AlbumCreate":
        if self.trip_start and self.trip_end and self.trip_end < self.trip_start:
            raise ValueError("Trip end date cannot be before the start date")
        return self


class AlbumPhotoResponse(TimestampedSchema):
    image_id: UUID
    caption: str | None
    position: int
    filename: str
    content_type: str
    public_url: str

    @classmethod
    def from_photo(cls, photo: object) -> "AlbumPhotoResponse":
        image = getattr(photo, "image")
        return cls(
            id=getattr(photo, "id"),
            created_at=getattr(photo, "created_at"),
            updated_at=getattr(photo, "updated_at"),
            image_id=getattr(photo, "image_id"),
            caption=getattr(photo, "caption"),
            position=getattr(photo, "position"),
            filename=getattr(image, "filename"),
            content_type=getattr(image, "content_type"),
            public_url=getattr(image, "public_url"),
        )


class AlbumResponse(TimestampedSchema):
    user_id: UUID
    title: str
    destination: str | None
    description: str | None
    trip_start: date | None
    trip_end: date | None
    photos: list[AlbumPhotoResponse] = Field(default_factory=list)

    @classmethod
    def from_album(cls, album: object) -> "AlbumResponse":
        return cls(
            id=getattr(album, "id"),
            created_at=getattr(album, "created_at"),
            updated_at=getattr(album, "updated_at"),
            user_id=getattr(album, "user_id"),
            title=getattr(album, "title"),
            destination=getattr(album, "destination"),
            description=getattr(album, "description"),
            trip_start=getattr(album, "trip_start"),
            trip_end=getattr(album, "trip_end"),
            photos=[AlbumPhotoResponse.from_photo(photo) for photo in getattr(album, "photos", [])],
        )
