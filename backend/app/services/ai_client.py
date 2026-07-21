from typing import Any

import httpx

from app.core.circuit_breaker import ai_circuit_breaker
from app.core.config import settings
from app.core.exceptions import AIServiceError
from app.core.http_retry import with_retries
from app.utils.json import extract_json_object


class AIClient:
    def __init__(self) -> None:
        self.api_key = (settings.groq_api_key or "").strip() or None
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = settings.groq_model
        self.provider = "groq"

    async def complete_json(self, system_prompt: str, user_prompt: str, *, image_data_url: str | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise AIServiceError("Groq API key is not configured")

        endpoint = "groq.chat.completions"
        ai_circuit_breaker.before_call(self.provider, endpoint=endpoint)

        user_content: Any = user_prompt
        if image_data_url:
            user_content = [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\nReturn only a valid JSON object."},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.4,
        }
        timeout = httpx.Timeout(settings.groq_timeout_seconds, connect=settings.http_connect_timeout_seconds)

        async def _call() -> dict[str, Any]:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                try:
                    content = data["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise AIServiceError("Groq returned an unexpected response shape") from exc
                if not isinstance(content, str) or not content.strip():
                    raise AIServiceError("Groq returned an empty response")
                try:
                    parsed = extract_json_object(content)
                except ValueError as exc:
                    raise AIServiceError("Groq returned malformed JSON") from exc
                if not isinstance(parsed, dict):
                    raise AIServiceError("Groq JSON was not an object")
                return parsed

        try:
            result = await with_retries(_call, provider=self.provider, endpoint=endpoint)
        except AIServiceError:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type="AIServiceError")
            raise
        except httpx.HTTPError as exc:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type=type(exc).__name__)
            raise AIServiceError(
                "We couldn't generate your itinerary right now. Please try again in a few minutes."
            ) from exc
        except Exception as exc:
            ai_circuit_breaker.record_failure(self.provider, endpoint=endpoint, error_type=type(exc).__name__)
            raise AIServiceError(
                "We couldn't generate your itinerary right now. Please try again in a few minutes."
            ) from exc

        ai_circuit_breaker.record_success(self.provider)
        return result
