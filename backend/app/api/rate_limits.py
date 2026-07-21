"""FastAPI dependencies that enforce per-feature rate limits.

Keying strategy:
  - Prefer authenticated ``user_id`` (stable, fair across devices)
  - Fall back to client IP for edge cases (should be rare — these endpoints
    already require auth, but IP covers misconfigured tokens / future public routes)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from app.auth.dependencies import CurrentUser
from app.core.config import settings
from app.core.rate_limit import check_rate_limit


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _client_key(request: Request, user_id: str | None) -> str:
    return f"user:{user_id}" if user_id else f"ip:{_client_ip(request)}"


async def limit_itinerary_generation(request: Request, current_user: CurrentUser) -> None:
    check_rate_limit(
        scope="itinerary",
        client_key=_client_key(request, str(current_user.id)),
        limit=settings.max_itinerary_requests_per_hour,
        endpoint="POST /itineraries/generate",
        user_id=str(current_user.id),
    )


async def limit_landmark_scan(request: Request, current_user: CurrentUser) -> None:
    check_rate_limit(
        scope="landmark_scan",
        client_key=_client_key(request, str(current_user.id)),
        limit=settings.max_scan_requests_per_hour,
        endpoint="POST /landmarks/recognize",
        user_id=str(current_user.id),
    )


async def limit_recommendations(request: Request, current_user: CurrentUser) -> None:
    check_rate_limit(
        scope="recommendations",
        client_key=_client_key(request, str(current_user.id)),
        limit=settings.max_recommendation_requests_per_hour,
        endpoint="POST /recommendations/generate",
        user_id=str(current_user.id),
    )


LimitItinerary = Annotated[None, Depends(limit_itinerary_generation)]
LimitLandmarkScan = Annotated[None, Depends(limit_landmark_scan)]
LimitRecommendations = Annotated[None, Depends(limit_recommendations)]
