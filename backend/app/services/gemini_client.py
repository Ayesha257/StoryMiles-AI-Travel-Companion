from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.utils.json import extract_json_object


class GeminiClient:
    """Vision client for landmark recognition via Google Gemini."""

    def __init__(self) -> None:
        self.api_key = (settings.gemini_api_key or "").strip() or None
        self.model = settings.gemini_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    async def complete_json_with_image(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        image_bytes: bytes,
        mime_type: str,
    ) -> dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("Gemini API key is not configured")

        import base64

        payload: dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": f"{system_prompt}\nReturn only a valid JSON object."}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": user_prompt},
                        {
                            "inlineData": {
                                "mimeType": mime_type,
                                "data": base64.b64encode(image_bytes).decode("ascii"),
                            }
                        },
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        url = f"{self.base_url}/models/{self.model}:generateContent"
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=10.0)) as client:
                response = await client.post(
                    url,
                    params={"key": self.api_key},
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                parts = data["candidates"][0]["content"]["parts"]
                # Thinking models may emit reasoning parts ("thought": true)
                # before the answer; only the non-thought parts hold the JSON.
                answer_texts = [
                    part.get("text", "")
                    for part in parts
                    if isinstance(part, dict) and not part.get("thought")
                ]
                text = "".join(answer_texts)
                if not text.strip():
                    raise AIServiceError("Gemini returned an empty response")
                try:
                    return extract_json_object(text)
                except ValueError:
                    for candidate_text in reversed(answer_texts):
                        try:
                            return extract_json_object(candidate_text)
                        except ValueError:
                            continue
                    raise
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            detail = str(exc)
            if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None:
                detail = f"{exc.response.status_code} {exc.response.text[:400]}"
            raise AIServiceError(f"Gemini request failed: {detail}") from exc
