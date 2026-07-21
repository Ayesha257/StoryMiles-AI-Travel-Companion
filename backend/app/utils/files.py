import re
import uuid
from pathlib import Path

from fastapi import UploadFile


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._")
    return cleaned or "upload"


def build_storage_key(filename: str) -> str:
    safe_name = sanitize_filename(filename)
    return f"{uuid.uuid4().hex}_{safe_name}"


async def read_upload_limited(upload: UploadFile, max_size_bytes: int) -> bytes:
    from app.core.config import settings

    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(1024 * 1024):
        total += len(chunk)
        if total > max_size_bytes:
            raise ValueError(f"Photo too large (max {settings.max_photo_size_mb}MB)")
        chunks.append(chunk)
    if total == 0:
        raise ValueError("Unsupported file type — empty file")
    return b"".join(chunks)
