from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse
from app.schemas.destination import DestinationCreate, DestinationResponse, DestinationUpdate
from app.schemas.image import ImageUploadResponse, LandmarkRecognitionResponse
from app.schemas.itinerary import ItineraryCreate, ItineraryGenerateRequest, ItineraryResponse, ItineraryUpdate
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.schemas.user import ProfileResponse, ProfileUpdate, UserResponse

__all__ = [name for name in globals() if not name.startswith("_")]
