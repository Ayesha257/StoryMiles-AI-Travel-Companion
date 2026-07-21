"""Shared HTTP retry helper for outbound AI providers.

Retry only transient failures (timeouts, connection errors, HTTP 429/5xx).
Do not retry 4xx validation/auth errors — those will not succeed on repeat
and would waste quota.

Backoff: base * 2^attempt (e.g. 0.5s, 1s) — classic exponential backoff
that gives the provider brief breathing room without long user waits.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx

from app.core.config import settings
from app.core.logging import log_event

logger = logging.getLogger("storymiles.http_retry")
T = TypeVar("T")


def is_transient_http_error(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.TransportError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        return status == 429 or status >= 500
    return False


async def with_retries(
    operation: Callable[[], Awaitable[T]],
    *,
    provider: str,
    endpoint: str,
    max_retries: int | None = None,
    backoff_base: float | None = None,
) -> T:
    retries = settings.ai_max_retries if max_retries is None else max_retries
    base = settings.ai_retry_backoff_base_seconds if backoff_base is None else backoff_base
    last_exc: BaseException | None = None

    for attempt in range(retries + 1):
        try:
            result = await operation()
            if attempt > 0:
                log_event(
                    logger,
                    logging.INFO,
                    "External call recovered after retry",
                    event="external_call_recovered",
                    endpoint=endpoint,
                    provider=provider,
                    recovered=True,
                    attempt=attempt + 1,
                )
            return result
        except Exception as exc:
            last_exc = exc
            transient = is_transient_http_error(exc)
            if not transient or attempt >= retries:
                log_event(
                    logger,
                    logging.ERROR,
                    "External call failed",
                    event="external_call_failed",
                    endpoint=endpoint,
                    provider=provider,
                    error_type=type(exc).__name__,
                    recovered=False,
                    attempt=attempt + 1,
                    extra={"detail": str(exc)[:400]},
                    exc_info=True,
                )
                raise
            delay = base * (2**attempt)
            log_event(
                logger,
                logging.WARNING,
                "External call transient failure — retrying",
                event="external_call_retry",
                endpoint=endpoint,
                provider=provider,
                error_type=type(exc).__name__,
                recovered=False,
                attempt=attempt + 1,
                extra={"backoff_seconds": delay, "detail": str(exc)[:400]},
            )
            await asyncio.sleep(delay)

    assert last_exc is not None
    raise last_exc
