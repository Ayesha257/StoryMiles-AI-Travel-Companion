from app.core.config import settings


def validate_image_metadata(filename: str | None, content_type: str | None) -> None:
    if not filename:
        raise ValueError("Uploaded file has no filename")
    if content_type not in settings.allowed_image_types:
        raise ValueError("Unsupported image content type")
