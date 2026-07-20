from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.repositories.destination import DestinationRepository
from app.repositories.image import ImageRepository
from app.repositories.itinerary import ItineraryRepository
from app.repositories.preferences import PreferencesRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.user import UserRepository
from app.services.ai_client import AIClient
from app.services.destination import DestinationService
from app.services.email_verification import EmailVerificationService
from app.services.gemini_client import GeminiClient
from app.services.history import HistoryService
from app.services.image import ImageUploadService
from app.services.itinerary import ItineraryGenerator
from app.services.landmark import LandmarkRecognitionService
from app.services.recommendation import RecommendationEngine
from app.services.user import UserService


def get_user_service(session: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    return UserService(UserRepository(session), PreferencesRepository(session))


def get_email_verification_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> EmailVerificationService:
    return EmailVerificationService(UserRepository(session))


def get_destination_service(session: Annotated[AsyncSession, Depends(get_db)]) -> DestinationService:
    return DestinationService(DestinationRepository(session))


def get_recommendation_engine(session: Annotated[AsyncSession, Depends(get_db)]) -> RecommendationEngine:
    return RecommendationEngine(RecommendationRepository(session))


def get_itinerary_generator(session: Annotated[AsyncSession, Depends(get_db)]) -> ItineraryGenerator:
    return ItineraryGenerator(AIClient(), ItineraryRepository(session))


def get_image_upload_service(session: Annotated[AsyncSession, Depends(get_db)]) -> ImageUploadService:
    return ImageUploadService(ImageRepository(session))


def get_landmark_recognition_service() -> LandmarkRecognitionService:
    return LandmarkRecognitionService(GeminiClient())


def get_history_service(session: Annotated[AsyncSession, Depends(get_db)]) -> HistoryService:
    return HistoryService(RecommendationRepository(session))


UserServiceDependency = Annotated[UserService, Depends(get_user_service)]
DestinationServiceDependency = Annotated[DestinationService, Depends(get_destination_service)]
RecommendationEngineDependency = Annotated[RecommendationEngine, Depends(get_recommendation_engine)]
ItineraryGeneratorDependency = Annotated[ItineraryGenerator, Depends(get_itinerary_generator)]
ImageUploadServiceDependency = Annotated[ImageUploadService, Depends(get_image_upload_service)]
LandmarkRecognitionDependency = Annotated[LandmarkRecognitionService, Depends(get_landmark_recognition_service)]
HistoryServiceDependency = Annotated[HistoryService, Depends(get_history_service)]
