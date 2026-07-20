from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_image_upload_service, get_landmark_recognition_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.models.enums import ImagePurpose
from app.schemas.image import LandmarkRecognitionResponse
from app.services.image import ImageUploadService
from app.services.landmark import LandmarkRecognitionService

router = APIRouter(prefix="/landmarks", tags=["Landmarks"])


@router.post("/recognize", response_model=LandmarkRecognitionResponse, status_code=status.HTTP_201_CREATED)
async def recognize_landmark(
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(...)],
    image_service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
    recognition_service: Annotated[LandmarkRecognitionService, Depends(get_landmark_recognition_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    try:
        image, image_bytes = await image_service.upload(current_user.id, file, ImagePurpose.LANDMARK_SCAN)
        result = await recognition_service.recognize(image_bytes, file.content_type or "image/jpeg")
        image = await image_service.set_recognition_result(image, result)
        await db.commit()
        return LandmarkRecognitionResponse.from_upload(image)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/{image_id}", response_model=LandmarkRecognitionResponse)
async def get_landmark_result(
    image_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> object:
    from app.repositories.image import ImageRepository

    image = await ImageRepository(db).get_for_user(image_id, current_user.id)
    if image is None or image.purpose != ImagePurpose.LANDMARK_SCAN:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Landmark scan not found")
    return LandmarkRecognitionResponse.from_upload(image)
