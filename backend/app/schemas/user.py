from datetime import date
from uuid import UUID

from pydantic import EmailStr, Field, HttpUrl

from app.schemas.common import Schema, TimestampedSchema


class ProfileUpdate(Schema):
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, max_length=3000)
    date_of_birth: date | None = None
    avatar_url: HttpUrl | None = None
    country: str | None = Field(default=None, max_length=100)
    city: str | None = Field(default=None, max_length=100)


class ProfileResponse(TimestampedSchema):
    user_id: UUID
    first_name: str | None
    last_name: str | None
    bio: str | None
    date_of_birth: date | None
    avatar_url: str | None
    country: str | None
    city: str | None


class UserResponse(TimestampedSchema):
    email: EmailStr
    is_active: bool
    is_verified: bool
    profile: ProfileResponse | None = None
