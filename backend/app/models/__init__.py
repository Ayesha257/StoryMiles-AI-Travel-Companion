from app.models.album import AlbumPhoto, TripAlbum
from app.models.destination import Destination
from app.models.image import ImageUpload
from app.models.itinerary import Itinerary
from app.models.preferences import UserPreferences
from app.models.recommendation import RecommendationHistory
from app.models.user import User, UserProfile

__all__ = [
    "AlbumPhoto",
    "Destination",
    "ImageUpload",
    "Itinerary",
    "RecommendationHistory",
    "TripAlbum",
    "User",
    "UserPreferences",
    "UserProfile",
]
