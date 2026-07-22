import pytest

from app.core.exceptions import AIServiceError
from app.services.ai_client import AIClient
from app.services.gemini_client import GeminiClient


@pytest.mark.asyncio
async def test_groq_client_fails_fast_without_api_key():
    client = AIClient()
    assert client.api_key is None
    with pytest.raises(AIServiceError, match="Groq API key is not configured"):
        await client.complete_json("system", "user")


@pytest.mark.asyncio
async def test_gemini_client_fails_fast_without_api_key():
    client = GeminiClient()
    assert client.api_key is None
    with pytest.raises(AIServiceError, match="Gemini API key is not configured"):
        await client.complete_json_with_image(
            "system",
            "user",
            image_bytes=b"fake",
            mime_type="image/jpeg",
        )
