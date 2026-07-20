from app.services.gemini_client import GeminiClient


LANDMARK_SYSTEM_PROMPT = (
    "You are StoryMiles' landmark guide. Identify the primary building or landmark in a travel photo. "
    "Be accurate and do not invent certainty — use null for unknown fields and keep confidence honest. "
    "Write for a traveler standing in front of the place: clear, vivid, and useful."
)

LANDMARK_USER_PROMPT = """
Identify the landmark in this photo and return ONLY a JSON object with this shape:
{
  "landmark_name": "string or null",
  "location": "city / area string or null",
  "country": "string or null",
  "confidence": 0.0,
  "description": "2-4 sentence overview of what this place is",
  "historical_background": "short historical background for travelers",
  "historical_facts": ["3-6 concrete historical facts"],
  "architecture_style": "string or null",
  "built_year": "string or null",
  "why_it_matters": "why travelers care about this place",
  "visitor_tips": ["3-6 practical tips: hours, tickets, best viewpoint, etiquette, nearby stops"],
  "best_time_to_visit": "string or null",
  "nearby_highlights": ["optional nearby places worth seeing"]
}

Rules:
- confidence must be a number between 0 and 1
- if you are unsure what the landmark is, set landmark_name to null and confidence below 0.6
- do not invent ticket prices or exact opening hours unless you are confident
""".strip()


class LandmarkRecognitionService:
    def __init__(self, gemini_client: GeminiClient | None = None) -> None:
        self.gemini_client = gemini_client or GeminiClient()

    async def recognize(self, image_bytes: bytes, content_type: str) -> dict:
        result = await self.gemini_client.complete_json_with_image(
            LANDMARK_SYSTEM_PROMPT,
            LANDMARK_USER_PROMPT,
            image_bytes=image_bytes,
            mime_type=content_type or "image/jpeg",
        )
        confidence = result.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1:
            result["confidence"] = 0.0
        else:
            result["confidence"] = float(confidence)

        for list_field in ("historical_facts", "visitor_tips", "nearby_highlights"):
            value = result.get(list_field)
            if not isinstance(value, list):
                result[list_field] = []
            else:
                result[list_field] = [str(item).strip() for item in value if str(item).strip()]

        for text_field in (
            "landmark_name",
            "location",
            "country",
            "description",
            "historical_background",
            "architecture_style",
            "built_year",
            "why_it_matters",
            "best_time_to_visit",
        ):
            value = result.get(text_field)
            if value is not None:
                text = str(value).strip()
                result[text_field] = text or None

        return result
