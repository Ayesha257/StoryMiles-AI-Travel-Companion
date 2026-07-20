import asyncio
from pathlib import Path
from uuid import UUID

from fastapi import UploadFile

from app.core.config import settings
from app.models.enums import ImagePurpose
from app.repositories.image import ImageRepository
from app.utils.files import build_storage_key, read_upload_limited


class ImageUploadService:
    def __init__(self, repository: ImageRepository) -> None:
        self.repository = repository
        self.upload_directory = Path(settings.upload_directory).resolve()

    async def upload(self, user_id: UUID, file: UploadFile, purpose: ImagePurpose) -> tuple[object, bytes]:
        if file.content_type not in settings.allowed_image_types:
            raise ValueError("Unsupported image content type")
        if not file.filename:
            raise ValueError("Uploaded file has no filename")
        content = await read_upload_limited(file, settings.max_upload_size_bytes)
        storage_key = build_storage_key(file.filename)
        target = self.upload_directory / storage_key
        await asyncio.to_thread(self.upload_directory.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(target.write_bytes, content)
        image = await self.repository.create(
            user_id=user_id,
            filename=file.filename,
            storage_key=storage_key,
            content_type=file.content_type,
            size_bytes=len(content),
            purpose=purpose,
            public_url=f"/uploads/{storage_key}",
        )
        return image, content

    async def set_recognition_result(self, image: object, result: dict) -> object:
        image.recognition_result = result
        await self.repository.session.flush()
        await self.repository.session.refresh(image)
        return image
