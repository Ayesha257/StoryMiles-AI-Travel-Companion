"""Structured logging helpers.

We keep Python's stdlib ``logging`` (already wired in the app) rather than
adding Winston/Pino equivalents. Reasons:
  - Zero new deps for the default path
  - Works with uvicorn's existing handlers
  - Optional JSON formatter for production log shippers

Every failure/rate-limit rejection should call ``log_event`` so fields are
consistent: timestamp (via asctime), endpoint, user_id, error_type, recovered.
"""

from __future__ import annotations

import json
import logging
import logging.config
from datetime import datetime, timezone
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "event",
            "endpoint",
            "user_id",
            "client_key",
            "error_type",
            "provider",
            "recovered",
            "attempt",
            "retry_after",
            "request_id",
            "extra",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", *, json_logs: bool = False) -> None:
    formatter_name = "json" if json_logs else "standard"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                },
                "json": {"()": "app.core.logging.JsonFormatter"},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_name,
                }
            },
            "root": {"handlers": ["console"], "level": level},
        }
    )


def log_event(
    logger: logging.Logger,
    level: int,
    message: str,
    *,
    event: str,
    endpoint: str | None = None,
    user_id: str | None = None,
    client_key: str | None = None,
    error_type: str | None = None,
    provider: str | None = None,
    recovered: bool | None = None,
    attempt: int | None = None,
    retry_after: int | None = None,
    request_id: str | None = None,
    extra: dict[str, Any] | None = None,
    exc_info: bool = False,
) -> None:
    logger.log(
        level,
        message,
        extra={
            "event": event,
            "endpoint": endpoint,
            "user_id": user_id,
            "client_key": client_key,
            "error_type": error_type,
            "provider": provider,
            "recovered": recovered,
            "attempt": attempt,
            "retry_after": retry_after,
            "request_id": request_id,
            "extra": extra or {},
        },
        exc_info=exc_info,
    )
