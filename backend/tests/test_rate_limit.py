from app.core.exceptions import RateLimitError
from app.core.rate_limit import InMemorySlidingWindow, check_rate_limit, format_wait, reset_in_memory_limits


def test_format_wait_humanizes_long_waits():
    assert format_wait(45) == "45 seconds"
    assert format_wait(1) == "1 second"
    assert format_wait(90) == "2 minutes"
    assert format_wait(3578) == "1 hour"
    assert format_wait(7200) == "2 hours"


def test_sliding_window_allows_under_limit():
    limiter = InMemorySlidingWindow()
    for _ in range(3):
        allowed, retry = limiter.hit("user:1", limit=3, window_seconds=3600)
        assert allowed is True
        assert retry == 0


def test_sliding_window_blocks_over_limit():
    limiter = InMemorySlidingWindow()
    for _ in range(2):
        limiter.hit("user:2", limit=2, window_seconds=3600)
    allowed, retry = limiter.hit("user:2", limit=2, window_seconds=3600)
    assert allowed is False
    assert retry >= 1


def test_check_rate_limit_raises_429_style_error():
    reset_in_memory_limits()
    for _ in range(2):
        check_rate_limit(
            scope="itinerary",
            client_key="user:test",
            limit=2,
            endpoint="POST /itineraries/generate",
            user_id="test",
            window_seconds=3600,
        )
    try:
        check_rate_limit(
            scope="itinerary",
            client_key="user:test",
            limit=2,
            endpoint="POST /itineraries/generate",
            user_id="test",
            window_seconds=3600,
        )
        assert False, "expected RateLimitError"
    except RateLimitError as exc:
        assert exc.status_code == 429
        assert exc.retry_after >= 1
        assert "seconds" not in exc.detail or "minute" in exc.detail or "hour" in exc.detail or "second" in exc.detail
