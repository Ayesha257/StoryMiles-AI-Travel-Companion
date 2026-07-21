from app.core.config import settings
from app.services.image_processing import detect_image_mime


def validate_image_metadata(filename: str | None, content_type: str | None) -> None:
    if not filename:
        raise ValueError("Unsupported file type — missing filename")
    if content_type and content_type not in settings.allowed_image_types:
        raise ValueError("Unsupported file type — use JPG, PNG, or WebP")


def validate_image_bytes(content: bytes) -> str:
    mime = detect_image_mime(content)
    if mime is None or mime not in settings.allowed_image_types:
        raise ValueError("Unsupported file type — use JPG, PNG, or WebP")
    if len(content) > settings.max_upload_size_bytes:
        raise ValueError(f"Photo too large (max {settings.max_photo_size_mb}MB)")
    return mime
