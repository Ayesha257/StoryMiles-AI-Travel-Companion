from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "StoryMiles API"
    environment: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://storymiles:storymiles@localhost:5432/storymiles"
    )
    database_echo: bool = False
    database_pool_size: int = Field(default=10, ge=1, le=100)
    database_max_overflow: int = Field(default=20, ge=0, le=100)
    database_pool_timeout: int = Field(default=30, ge=1)

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=30, ge=1, le=365)

    cors_origins: list[AnyHttpUrl] = []
    cors_allow_credentials: bool = True

    upload_directory: str = "uploads"
    # Prefer MB-based env knobs for ops; bytes field remains for internal readers.
    max_photo_size_mb: int = Field(default=10, ge=1, le=50)
    max_photos_per_album: int = Field(default=50, ge=1, le=500)
    max_storage_per_user_mb: int = Field(default=500, ge=10, le=10_000)
    max_upload_batch_size: int = Field(default=10, ge=1, le=50)
    # Compression: 1920px is enough for gallery + PDF + Gemini; JPEG 85 keeps
    # artifacts low while cutting multi-megabyte phone photos dramatically.
    image_max_dimension: int = Field(default=1920, ge=640, le=4096)
    image_jpeg_quality: int = Field(default=85, ge=60, le=95)
    allowed_image_types: set[str] = {"image/jpeg", "image/png", "image/webp"}

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_photo_size_mb * 1024 * 1024

    @property
    def max_storage_per_user_bytes(self) -> int:
        return self.max_storage_per_user_mb * 1024 * 1024

    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"

    # Landmark scanner uses Gemini vision. Itineraries continue to use Groq.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.5-flash"

    # SMTP delivery for registration verification codes.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "StoryMiles"
    verification_code_expire_minutes: int = Field(default=10, ge=2, le=60)
    verification_resend_cooldown_seconds: int = Field(default=60, ge=15, le=600)

    # --- Rate limiting (per user_id, or client IP when unauthenticated) ---
    # Sliding window: fairer than fixed windows at hour boundaries; easy to reason about for cost caps.
    max_itinerary_requests_per_hour: int = Field(default=5, ge=1, le=100)
    max_scan_requests_per_hour: int = Field(default=10, ge=1, le=200)
    max_recommendation_requests_per_hour: int = Field(default=30, ge=1, le=500)
    rate_limit_window_seconds: int = Field(default=3600, ge=60, le=86400)

    # Optional Redis URL for multi-instance deployments. Empty = in-process memory.
    redis_url: str | None = None

    # --- External API timeouts (seconds) ---
    # Groq JSON itineraries are usually fast; 15s catches hangs without waiting forever.
    groq_timeout_seconds: float = Field(default=15.0, ge=3.0, le=120.0)
    # Gemini vision needs more headroom for image upload + multimodal decode.
    gemini_timeout_seconds: float = Field(default=20.0, ge=5.0, le=180.0)
    # Connect timeout shared by outbound HTTP clients.
    http_connect_timeout_seconds: float = Field(default=5.0, ge=1.0, le=30.0)

    # --- Retries (transient failures only: timeouts, 5xx, network) ---
    # 2 retries = 3 total attempts. Enough for brief blips; avoids multiplying billable calls.
    ai_max_retries: int = Field(default=2, ge=0, le=5)
    ai_retry_backoff_base_seconds: float = Field(default=0.5, ge=0.1, le=5.0)

    # --- Circuit breaker (provider-wide) ---
    # If error rate spikes, trip open so we stop burning budget and show a maintenance message.
    circuit_breaker_failure_threshold: int = Field(default=8, ge=2, le=100)
    circuit_breaker_window_seconds: int = Field(default=120, ge=30, le=3600)
    circuit_breaker_open_seconds: int = Field(default=300, ge=30, le=3600)

    # --- Observability ---
    # Optional Sentry DSN (free tier). Leave empty to disable.
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    # JSON logs are easier to ship to a log aggregator in production.
    log_json: bool = False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
