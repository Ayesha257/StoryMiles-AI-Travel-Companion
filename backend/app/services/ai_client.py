from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceError
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
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return extract_json_object(content)
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise AIServiceError(f"Groq request failed: {exc}") from exc
