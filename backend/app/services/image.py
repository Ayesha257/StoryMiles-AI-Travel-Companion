import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core.config import settings
from app.models.enums import ImagePurpose
from app.repositories.image import ImageRepository
from app.services.image_processing import validate_and_compress_image
from app.utils.files import build_storage_key, read_upload_limited


class ImageUploadService:
    def __init__(self, repository: ImageRepository) -> None:
        self.repository = repository
        self.upload_directory = Path(settings.upload_directory).resolve()

    async def ensure_user_storage_available(self, user_id: UUID, *, incoming_bytes: int = 0) -> None:
        used = await self.repository.total_size_bytes_for_user(user_id)
        if used + incoming_bytes > settings.max_storage_per_user_bytes:
            raise ValueError(
                f"Storage limit reached (max {settings.max_storage_per_user_mb}MB per account)"
            )

    async def upload(self, user_id: UUID, file: UploadFile, purpose: ImagePurpose) -> tuple[object, bytes]:
        if not file.filename:
            raise ValueError("Unsupported file type — missing filename")

        # Read with a hard byte cap BEFORE decoding — rejects oversized payloads early.
        raw = await read_upload_limited(file, settings.max_upload_size_bytes)
        processed = await asyncio.to_thread(
            validate_and_compress_image,
            raw,
            original_filename=file.filename,
            declared_content_type=file.content_type,
        )

        await self.ensure_user_storage_available(user_id, incoming_bytes=len(processed.content))

        # Always store with .jpg after compression so the key matches content.
        storage_key = build_storage_key(processed.filename)
        target = self.upload_directory / storage_key
        await asyncio.to_thread(self.upload_directory.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, processed.content)

        image = await self.repository.create(
            user_id=user_id,
            filename=processed.filename,
            storage_key=storage_key,
            content_type=processed.content_type,
            size_bytes=len(processed.content),
            purpose=purpose,
            public_url=f"/uploads/{storage_key}",
        )
        return image, processed.content

    async def set_recognition_result(self, image: object, result: dict) -> object:
        image.recognition_result = result
        await self.repository.session.flush()
        await self.repository.session.refresh(image)
        return image
