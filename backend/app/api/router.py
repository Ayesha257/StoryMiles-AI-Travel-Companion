from fastapi import APIRouter

from app.api import albums, auth, destinations, images, itinerary, landmark, legacy, preferences, recommendations, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(preferences.router)
api_router.include_router(destinations.router)
api_router.include_router(recommendations.router)
api_router.include_router(itinerary.router)
api_router.include_router(landmark.router)
api_router.include_router(images.router)
api_router.include_router(albums.router)
api_router.include_router(legacy.router)
