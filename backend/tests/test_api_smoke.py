def test_health_endpoint_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "recommendation_model" in body
    assert "circuits" in body
    assert "groq" in body["circuits"]
    assert "gemini" in body["circuits"]


def test_itinerary_generate_returns_502_without_groq_key(authed_client):
    """Reproduces the exact failure seen in local testing when GROQ_API_KEY is empty."""
    response = authed_client.post(
        "/api/v1/itineraries/generate",
        json={
            "destination": "Paris",
            "country": "France",
            "days": 3,
            "budget_level": "medium",
            "interests": ["culture"],
        },
    )
    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "Groq API key is not configured" in detail


def test_itinerary_generate_requires_auth(client):
    response = client.post(
        "/api/v1/itineraries/generate",
        json={
            "destination": "Paris",
            "country": "France",
            "days": 3,
            "budget_level": "medium",
            "interests": ["culture"],
        },
    )
    assert response.status_code == 401


def test_login_rejects_bad_payload(client):
    response = client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "x"})
    assert response.status_code == 422
