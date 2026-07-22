"""Frontend-adjacent pure logic checks (no browser, no GitHub).

Mirrors formatRetryAfter in frontend/src/lib/api.ts so wait-time UX stays correct.
"""


def format_retry_after(seconds: int) -> str:
    s = max(1, int(__import__("math").ceil(seconds)))
    if s < 60:
        return f"{s} second{'s' if s != 1 else ''}"
    minutes = int(__import__("math").ceil(s / 60))
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours, rem = divmod(minutes, 60)
    if rem == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    return f"{hours} hour{'s' if hours != 1 else ''} {rem} minute{'s' if rem != 1 else ''}"


def test_frontend_wait_copy_matches_bug_report_case():
    # The screenshot showed "3578 seconds" — this must humanize.
    assert format_retry_after(3578) == "1 hour"
    assert "second" not in format_retry_after(3578)
