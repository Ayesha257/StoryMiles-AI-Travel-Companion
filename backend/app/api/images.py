from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_image_upload_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.models.enums import ImagePurpose
from app.repositories.image import ImageRepository
from app.schemas.image import ImageUploadResponse
from app.services.image import ImageUploadService

router = APIRouter(prefix="/images", tags=["Images"])


@router.post("", response_model=ImageUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_image(
    current_user: CurrentUser,
    file: Annotated[UploadFile, File(...)],
    service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
    purpose: ImagePurpose = ImagePurpose.ITINERARY,
) -> object:
    try:
        image, _ = await service.upload(current_user.id, file, purpose)
        await db.commit()
        return image
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("", response_model=list[ImageUploadResponse])
async def list_images(current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)], offset: int = 0, limit: int = 100) -> object:
    return await ImageRepository(db).list_for_user(current_user.id, offset=max(offset, 0), limit=min(max(limit, 1), 100))


@router.get("/{image_id}", response_model=ImageUploadResponse)
async def get_image(image_id: UUID, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]) -> object:
    image = await ImageRepository(db).get_for_user(image_id, current_user.id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image
