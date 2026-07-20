"""Legacy API path aliases from the original contract (deprecated)."""

from fastapi import APIRouter

from app.api import itinerary, landmark, preferences, recommendations
from app.schemas.itinerary import ItineraryResponse
from app.schemas.image import LandmarkRecognitionResponse
from app.schemas.preferences import PreferencesResponse
from app.schemas.recommendation import RecommendationResponse

router = APIRouter()

router.add_api_route(
    "/preferences",
    preferences.update_preferences,
    methods=["POST"],
    response_model=PreferencesResponse,
    deprecated=True,
    name="legacy_store_preferences",
)
router.add_api_route(
    "/recommendations",
    recommendations.list_history,
    methods=["GET"],
    response_model=list[RecommendationResponse],
    deprecated=True,
    name="legacy_list_recommendations",
)
router.add_api_route(
    "/landmark/identify",
    landmark.recognize_landmark,
    methods=["POST"],
    response_model=LandmarkRecognitionResponse,
    deprecated=True,
    name="legacy_identify_landmark",
)
router.add_api_route(
    "/itinerary/generate",
    itinerary.generate_itinerary,
    methods=["POST"],
    response_model=ItineraryResponse,
    deprecated=True,
    name="legacy_generate_itinerary",
)
router.add_api_route(
    "/itinerary/history",
    itinerary.list_itineraries,
    methods=["GET"],
    response_model=list[ItineraryResponse],
    deprecated=True,
    name="legacy_itinerary_history",
)
