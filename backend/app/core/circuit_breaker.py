"""Provider-level circuit breaker for Groq / Gemini.

Why: per-user rate limits stop one abuser; a circuit breaker stops a provider
outage or error storm from draining the rest of the monthly budget while every
request retries and fails.

Algorithm: count failures in a rolling window. When failures >= threshold,
open the circuit for ``open_seconds`` and reject new calls with 503 until it
half-opens (after cooldown) and a probe succeeds.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import log_event

logger = logging.getLogger("storymiles.circuit")


class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int | None = None,
        window_seconds: int | None = None,
        open_seconds: int | None = None,
    ) -> None:
        self.failure_threshold = failure_threshold or settings.circuit_breaker_failure_threshold
        self.window_seconds = window_seconds or settings.circuit_breaker_window_seconds
        self.open_seconds = open_seconds or settings.circuit_breaker_open_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._opened_at: dict[str, float] = {}
        self._lock = threading.Lock()

    def _prune(self, provider: str, now: float) -> None:
        window = self._failures[provider]
        while window and now - window[0] > self.window_seconds:
            window.popleft()

    def before_call(self, provider: str, *, endpoint: str | None = None) -> None:
        with self._lock:
            now = time.time()
            opened = self._opened_at.get(provider)
            if opened is not None:
                elapsed = now - opened
                if elapsed < self.open_seconds:
                    retry_after = int(self.open_seconds - elapsed) + 1
                    log_event(
                        logger,
                        logging.WARNING,
                        "Circuit breaker open — rejecting call",
                        event="circuit_open_reject",
                        endpoint=endpoint,
                        provider=provider,
                        error_type="ServiceUnavailableError",
                        retry_after=retry_after,
                    )
                    raise ServiceUnavailableError(
                        f"{provider.capitalize()} is temporarily unavailable while we recover. "
                        f"Please try again in about {retry_after} seconds.",
                        retry_after=retry_after,
                    )
                # Cooldown elapsed — allow a probe (half-open).
                del self._opened_at[provider]

    def record_success(self, provider: str) -> None:
        with self._lock:
            self._failures[provider].clear()
            self._opened_at.pop(provider, None)

    def record_failure(self, provider: str, *, endpoint: str | None = None, error_type: str | None = None) -> None:
        with self._lock:
            now = time.time()
            self._prune(provider, now)
            self._failures[provider].append(now)
            if len(self._failures[provider]) >= self.failure_threshold:
                self._opened_at[provider] = now
                log_event(
                    logger,
                    logging.ERROR,
                    "Circuit breaker tripped open",
                    event="circuit_tripped",
                    endpoint=endpoint,
                    provider=provider,
                    error_type=error_type or "provider_failure",
                    retry_after=self.open_seconds,
                    extra={"failures_in_window": len(self._failures[provider])},
                )

    def status(self, provider: str) -> dict[str, object]:
        with self._lock:
            now = time.time()
            self._prune(provider, now)
            opened = self._opened_at.get(provider)
            return {
                "provider": provider,
                "open": opened is not None and (now - opened) < self.open_seconds,
                "failures_in_window": len(self._failures[provider]),
                "opened_at": opened,
            }


# Shared breakers for the two paid AI providers.
ai_circuit_breaker = CircuitBreaker()
