"""Shared fixtures for StoryMiles API automation tests.

Runs locally without GitHub. Does not commit or push anything.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Ensure a stable JWT secret before app settings are imported.
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-at-least-32-characters-long!!",
)
os.environ.setdefault("ENVIRONMENT", "test")
# Force empty AI keys so missing-config paths are deterministic in unit/API tests.
os.environ["GROQ_API_KEY"] = ""
os.environ["GEMINI_API_KEY"] = ""


@pytest.fixture(autouse=True)
def _clear_rate_limits() -> Generator[None, None, None]:
    from app.core.rate_limit import reset_in_memory_limits

    reset_in_memory_limits()
    yield
    reset_in_memory_limits()


@pytest.fixture
def app():
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def verified_user() -> MagicMock:
    user = MagicMock()
    user.id = uuid4()
    user.email = "tester@example.com"
    user.is_active = True
    user.is_verified = True
    return user


@pytest.fixture
def authed_client(app, verified_user) -> Generator[TestClient, None, None]:
    """Authenticated client with AI + rate-limit deps overridden for isolation."""
    from app.api.rate_limits import (
        limit_itinerary_generation,
        limit_landmark_scan,
        limit_recommendations,
    )
    from app.auth.dependencies import get_current_user
    from app.api.dependencies import get_itinerary_generator, get_landmark_recognition_service
    from app.services.ai_client import AIClient
    from app.services.itinerary import ItineraryGenerator

    async def _user():
        return verified_user

    async def _allow_limit():
        return None

    def _itinerary_generator():
        # Real AIClient (empty key) + mock repo: fails before any DB write.
        return ItineraryGenerator(AIClient(), AsyncMock())

    app.dependency_overrides[get_current_user] = _user
    app.dependency_overrides[limit_itinerary_generation] = _allow_limit
    app.dependency_overrides[limit_landmark_scan] = _allow_limit
    app.dependency_overrides[limit_recommendations] = _allow_limit
    app.dependency_overrides[get_itinerary_generator] = _itinerary_generator

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
