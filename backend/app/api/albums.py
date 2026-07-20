import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_image_upload_service
from app.auth.dependencies import CurrentUser
from app.database.session import get_db
from app.models.enums import ImagePurpose
from app.repositories.album import AlbumRepository
from app.schemas.album import AlbumCreate, AlbumPhotoResponse, AlbumResponse
from app.services.album_pdf import AlbumPDFService
from app.services.image import ImageUploadService

router = APIRouter(prefix="/albums", tags=["Trip Albums"])


@router.get("", response_model=list[AlbumResponse])
async def list_albums(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AlbumResponse]:
    albums = await AlbumRepository(db).list_for_user(current_user.id)
    return [AlbumResponse.from_album(album) for album in albums]


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    request: AlbumCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlbumResponse:
    repository = AlbumRepository(db)
    album = await repository.create(user_id=current_user.id, **request.persisted_values())
    await db.commit()
    album = await repository.get_for_user(album.id, current_user.id)
    return AlbumResponse.from_album(album)


@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(
    album_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlbumResponse:
    album = await AlbumRepository(db).get_for_user(album_id, current_user.id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return AlbumResponse.from_album(album)


@router.post("/{album_id}/photos", response_model=list[AlbumPhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_album_photos(
    album_id: UUID,
    current_user: CurrentUser,
    files: Annotated[list[UploadFile], File(...)],
    service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AlbumPhotoResponse]:
    repository = AlbumRepository(db)
    album = await repository.get_for_user(album_id, current_user.id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    if not files:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose at least one photo")
    if len(files) > 30:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Upload up to 30 photos at a time")

    try:
        for upload in files:
            image, _ = await service.upload(current_user.id, upload, ImagePurpose.ALBUM)
            await repository.add_photo(album.id, image.id)
        await db.commit()
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    refreshed = await repository.get_for_user(album_id, current_user.id)
    return [AlbumPhotoResponse.from_photo(photo) for photo in refreshed.photos]


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    repository = AlbumRepository(db)
    album = await repository.get_for_user(album_id, current_user.id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    await repository.delete(album)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{album_id}/pdf")
async def download_album_pdf(
    album_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    album = await AlbumRepository(db).get_for_user(album_id, current_user.id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    if not album.photos:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Add photos before downloading a PDF")

    pdf = await AlbumPDFService().generate(album)
    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", album.title).strip("-").lower() or "trip-album"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}.pdf"'},
    )
