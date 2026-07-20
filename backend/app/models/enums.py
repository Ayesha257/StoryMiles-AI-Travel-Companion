from enum import StrEnum

from sqlalchemy import Enum


def pg_enum(enum_cls: type[StrEnum], name: str, **kwargs) -> Enum:
    return Enum(enum_cls, name=name, values_callable=lambda members: [member.value for member in members], **kwargs)


class TravelStyle(StrEnum):
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    FOOD = "food"
    LUXURY = "luxury"
    NATURE = "nature"
    RELAXATION = "relaxation"
    BUDGET = "budget"
    FAMILY = "family"


class BudgetLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    LUXURY = "luxury"


class TripStatus(StrEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ImagePurpose(StrEnum):
    PROFILE = "profile"
    LANDMARK_SCAN = "landmark_scan"
    ITINERARY = "itinerary"
    ALBUM = "album"


class RecommendationStatus(StrEnum):
    GENERATED = "generated"
    SAVED = "saved"
    DISMISSED = "dismissed"
