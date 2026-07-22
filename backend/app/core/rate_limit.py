"""Per-user / per-IP sliding-window rate limiter.

Why sliding window (not fixed bucket / token bucket)?
  - Matches product language: "N requests per hour"
  - Avoids the classic fixed-window burst at midnight/hour boundaries
  - Simple to reason about for cost control on Groq/Gemini

Backend:
  - Default: in-process memory (fine for a single uvicorn worker)
  - Optional Redis (REDIS_URL): shared across workers/instances — swap by setting
    the env var; no code change at call sites.

Rejection logging includes user_id/client_key, endpoint, and retry_after so
abuse patterns are visible in production logs.
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Protocol

from app.core.config import settings
from app.core.exceptions import RateLimitError
from app.core.logging import log_event

logger = logging.getLogger("storymiles.ratelimit")


class RateLimiterBackend(Protocol):
    def hit(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Record a hit. Returns (allowed, retry_after_seconds)."""


class InMemorySlidingWindow:
    """Process-local sliding window. Not shared across workers."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        window = self._hits[key]
        while window and now - window[0] > window_seconds:
            window.popleft()
        if len(window) >= limit:
            retry_after = int(window_seconds - (now - window[0])) + 1
            return False, max(retry_after, 1)
        window.append(now)
        return True, 0


class RedisSlidingWindow:
    """
    Redis sorted-set sliding window (drop-in when REDIS_URL is set).

    Requires: pip install redis
    Keys expire after the window so abandoned clients do not leak memory.
    """

    def __init__(self, redis_url: str) -> None:
        import redis

        self._r = redis.from_url(redis_url, decode_responses=True)

    def hit(self, key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.time()
        redis_key = f"rl:{key}"
        pipe = self._r.pipeline()
        pipe.zremrangebyscore(redis_key, 0, now - window_seconds)
        pipe.zcard(redis_key)
        pipe.zrange(redis_key, 0, 0, withscores=True)
        _, count, oldest = pipe.execute()
        if count >= limit:
            oldest_ts = float(oldest[0][1]) if oldest else now
            retry_after = int(window_seconds - (now - oldest_ts)) + 1
            return False, max(retry_after, 1)
        member = f"{now}:{time.time_ns()}"
        pipe = self._r.pipeline()
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, window_seconds + 5)
        pipe.execute()
        return True, 0


def _build_backend() -> RateLimiterBackend:
    url = (settings.redis_url or "").strip()
    if url:
        try:
            backend: RateLimiterBackend = RedisSlidingWindow(url)
            logger.info("Rate limiter using Redis backend")
            return backend
        except Exception:
            logger.exception("Failed to init Redis rate limiter; falling back to in-memory")
    logger.info("Rate limiter using in-memory backend (set REDIS_URL for multi-instance)")
    return InMemorySlidingWindow()


_backend = _build_backend()


def check_rate_limit(
    *,
    scope: str,
    client_key: str,
    limit: int,
    endpoint: str,
    user_id: str | None = None,
    window_seconds: int | None = None,
) -> None:
    """
    Enforce a sliding-window quota for ``scope:client_key``.

    Raises RateLimitError with retry_after when exceeded.
    """
    window = window_seconds or settings.rate_limit_window_seconds
    composite = f"{scope}:{client_key}"
    allowed, retry_after = _backend.hit(composite, limit=limit, window_seconds=window)
    if allowed:
        return

    log_event(
        logger,
        logging.WARNING,
        "Rate limit exceeded",
        event="rate_limit_rejected",
        endpoint=endpoint,
        user_id=user_id,
        client_key=client_key,
        error_type="RateLimitError",
        retry_after=retry_after,
        extra={"scope": scope, "limit": limit, "window_seconds": window},
    )
    raise RateLimitError(
        f"Too many requests for this feature. Please try again in about {format_wait(retry_after)}.",
        retry_after=retry_after,
    )


def format_wait(seconds: int) -> str:
    """Human-readable wait (avoid raw '3578 seconds' in API/UI copy)."""
    s = max(1, int(seconds))
    if s < 60:
        return f"{s} second{'s' if s != 1 else ''}"
    minutes = (s + 59) // 60
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours, rem = divmod(minutes, 60)
    if rem == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{hours} hour{'s' if hours != 1 else ''} {rem} minute{'s' if rem != 1 else ''}"


def reset_in_memory_limits() -> None:
    """Clear process-local counters (dev/testing). No-op for Redis backend."""
    if isinstance(_backend, InMemorySlidingWindow):
        _backend._hits.clear()
        logger.info("Cleared in-memory rate limit windows")
