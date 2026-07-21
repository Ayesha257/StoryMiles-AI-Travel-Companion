"""Image sniffing, validation, and compression helpers.

Compression choices (defensible defaults):
  - Cap longest edge at 1920px: matches Full HD displays and is more than
    enough for gallery grids, PDF keepsakes, and Gemini vision (which downsamples
    further). Phone cameras often shoot 12MP+; storing those raw wastes disk.
  - Re-encode as JPEG quality 85: widely compatible (incl. ReportLab PDFs),
    visually near-lossless for travel photos, typically 5–10× smaller than
    original HEIC/PNG/JPEG phone dumps.
  - Strip EXIF on save: reduces privacy leak risk (GPS) and file size.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, UnidentifiedImageError

from app.core.config import settings

# Magic-byte signatures — never trust Content-Type or file extension alone.
_JPEG_MAGIC = (b"\xff\xd8\xff",)
_PNG_MAGIC = (b"\x89PNG\r\n\x1a\n",)
# WebP is RIFF....WEBP
_WEBP_RIFF = b"RIFF"
_WEBP_WEBP = b"WEBP"

MIME_JPEG = "image/jpeg"
MIME_PNG = "image/png"
MIME_WEBP = "image/webp"


@dataclass(frozen=True)
class ProcessedImage:
    content: bytes
    content_type: str
    filename: str
    width: int
    height: int


def detect_image_mime(content: bytes) -> str | None:
    if len(content) < 12:
        return None
    if any(content.startswith(sig) for sig in _JPEG_MAGIC):
        return MIME_JPEG
    if any(content.startswith(sig) for sig in _PNG_MAGIC):
        return MIME_PNG
    if content[:4] == _WEBP_RIFF and content[8:12] == _WEBP_WEBP:
        return MIME_WEBP
    return None


def validate_and_compress_image(
    content: bytes,
    *,
    original_filename: str,
    declared_content_type: str | None = None,
) -> ProcessedImage:
    """
    Validate magic bytes + decode with Pillow, then resize/compress.

    Raises ValueError with user-facing messages on failure.
    """
    max_bytes = settings.max_upload_size_bytes
    if len(content) > max_bytes:
        raise ValueError(f"Photo too large (max {settings.max_photo_size_mb}MB)")

    detected = detect_image_mime(content)
    if detected is None:
        raise ValueError("Unsupported file type — use JPG, PNG, or WebP")
    if detected not in settings.allowed_image_types:
        raise ValueError("Unsupported file type — use JPG, PNG, or WebP")

    # Declared type is informational only; magic bytes win. Mismatch is still allowed
    # if the bytes are a real image (common with some mobile browsers).
    _ = declared_content_type

    try:
        with Image.open(io.BytesIO(content)) as img:
            img.load()
            # Normalize orientation from EXIF before stripping metadata.
            img = _apply_exif_orientation(img)
            img = img.convert("RGB")
            max_dim = settings.image_max_dimension
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            width, height = img.size
            buffer = io.BytesIO()
            img.save(
                buffer,
                format="JPEG",
                quality=settings.image_jpeg_quality,
                optimize=True,
                progressive=True,
            )
            compressed = buffer.getvalue()
    except UnidentifiedImageError as exc:
        raise ValueError("Unsupported file type — use JPG, PNG, or WebP") from exc
    except OSError as exc:
        raise ValueError("Could not process this image — try another photo") from exc

    if len(compressed) > max_bytes:
        # Extremely rare after resize; still guard storage.
        raise ValueError(f"Photo too large after compression (max {settings.max_photo_size_mb}MB)")

    stem = original_filename.rsplit(".", 1)[0] if original_filename else "photo"
    filename = f"{stem}.jpg"
    return ProcessedImage(
        content=compressed,
        content_type=MIME_JPEG,
        filename=filename,
        width=width,
        height=height,
    )


def _apply_exif_orientation(img: Image.Image) -> Image.Image:
    try:
        exif = img.getexif()
        orientation = exif.get(274) if exif else None
    except Exception:
        return img
    # Pillow 10+ has ImageOps.exif_transpose
    try:
        from PIL import ImageOps

        return ImageOps.exif_transpose(img) or img
    except Exception:
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            return img.rotate(rotations[orientation], expand=True)
        return img
