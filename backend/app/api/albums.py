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
from app.core.config import settings
from app.schemas.album import (
    AlbumCreate,
    AlbumPhotoResponse,
    AlbumPhotoUploadBatchResponse,
    AlbumPhotoUploadItemResult,
    AlbumResponse,
)
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


@router.post("/{album_id}/photos", response_model=AlbumPhotoUploadBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_album_photos(
    album_id: UUID,
    current_user: CurrentUser,
    files: Annotated[list[UploadFile], File(...)],
    service: Annotated[ImageUploadService, Depends(get_image_upload_service)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AlbumPhotoUploadBatchResponse:
    repository = AlbumRepository(db)
    album = await repository.get_for_user(album_id, current_user.id)
    if album is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    if not files:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Choose at least one photo")
    if len(files) > settings.max_upload_batch_size:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Upload up to {settings.max_upload_batch_size} photos at a time",
        )

    results: list[AlbumPhotoUploadItemResult] = []
    photo_count = await repository.count_photos(album_id)

    for upload in files:
        filename = upload.filename or "photo"
        if photo_count >= settings.max_photos_per_album:
            results.append(
                AlbumPhotoUploadItemResult(
                    filename=filename,
                    ok=False,
                    error=f"Album full (max {settings.max_photos_per_album} photos)",
                )
            )
            continue
        try:
            image, _ = await service.upload(current_user.id, upload, ImagePurpose.ALBUM)
            photo = await repository.add_photo(album.id, image.id)
            # Need image relationship for response shape
            photo.image = image
            results.append(
                AlbumPhotoUploadItemResult(
                    filename=filename,
                    ok=True,
                    photo=AlbumPhotoResponse.from_photo(photo),
                )
            )
            photo_count += 1
            await db.commit()
        except ValueError as exc:
            await db.rollback()
            results.append(AlbumPhotoUploadItemResult(filename=filename, ok=False, error=str(exc)))
        except Exception:
            await db.rollback()
            results.append(
                AlbumPhotoUploadItemResult(
                    filename=filename,
                    ok=False,
                    error="Could not upload this photo — try again",
                )
            )

    refreshed = await repository.get_for_user(album_id, current_user.id)
    succeeded = sum(1 for item in results if item.ok)
    failed = len(results) - succeeded
    if succeeded == 0 and failed > 0:
        # All failed — still 422 so clients can show the first specific error.
        first_error = next((item.error for item in results if item.error), "Upload failed")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=first_error)

    return AlbumPhotoUploadBatchResponse(
        results=results,
        photos=[AlbumPhotoResponse.from_photo(photo) for photo in refreshed.photos] if refreshed else [],
        succeeded=succeeded,
        failed=failed,
    )


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
