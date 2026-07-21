from typing import Any

import httpx

from app.core.circuit_breaker import ai_circuit_breaker
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.http_retry import with_retries
from app.utils.json import extract_json_object


class GeminiClient:
    """Vision client for landmark recognition via Google Gemini."""

    def __init__(self) -> None:
        self.api_key = (settings.gemini_api_key or "").strip() or None
        self.model = settings.gemini_model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.provider = "gemini"

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

        endpoint = "gemini.generateContent"
        ai_circuit_breaker.before_call(self.provider, endpoint=endpoint)

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
        timeout = httpx.Timeout(settings.gemini_timeout_seconds, connect=settings.http_connect_timeout_seconds)

        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    params={"key": self.api_key},
                    headers={"Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                try:
                    parts = data["candidates"][0]["content"]["parts"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise AIServiceError("Gemini returned an unexpected response shape") from exc
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
                    parsed = extract_json_object(text)
                except ValueError:
                    parsed = None
                    for candidate_text in reversed(answer_texts):
                        try:
                            parsed = extract_json_object(candidate_text)
                            break
                        except ValueError:
                            continue
                    if parsed is None:
                        raise AIServiceError("Gemini returned malformed JSON") from None
                if not isinstance(parsed, dict):
                    raise AIServiceError("Gemini JSON was not an object")
                return parsed

        try:
            result = await with_retries(_call, provider=self.provider, endpoint=endpoint)
        except AIServiceError:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type="AIServiceError")
            raise AIServiceError(
                "We couldn't identify this landmark. Try a clearer photo, or try again in a few minutes."
            ) from None
        except httpx.HTTPError as exc:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type=type(exc).__name__)
            raise AIServiceError(
                "We couldn't identify this landmark. Try a clearer photo, or try again in a few minutes."
            ) from exc
        except Exception as exc:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type=type(exc).__name__)
            raise AIServiceError(
                "We couldn't identify this landmark. Try a clearer photo, or try again in a few minutes."
            ) from exc

        ai_circuit_breaker.record_success(self.provider)
        return result
