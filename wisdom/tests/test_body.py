"""Tests for WISDOM Body module — API endpoints."""

import os

import pytest
from fastapi.testclient import TestClient

from wisdom.body.api import app


def _llm_available() -> bool:
    """Check if any LLM backend is reachable for integration tests."""
    if os.getenv("GOOGLE_API_KEY", ""):
        return True
    try:
        import httpx
        resp = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        if resp.status_code == 200:
            models = [m.get("name", "") for m in resp.json().get("models", [])]
            return any("llama" in m for m in models)
    except Exception:
        pass
    return False


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
        assert "llm" in data


class TestProfileEndpoints:
    def test_get_nonexistent_profile(self, client):
        response = client.get("/api/v1/profile/nonexistent")
        assert response.status_code == 404

    @pytest.mark.skipif(
        not _llm_available(),
        reason="Requires a running LLM (Ollama with model or GOOGLE_API_KEY)",
    )
    def test_chat_creates_profile(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"user_id": "test_api_user", "message": "Hello!"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


class TestFeedbackEndpoint:
    def test_submit_feedback(self, client):
        response = client.post(
            "/api/v1/feedback",
            json={"rating": 5, "comment": "Great!"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "received"
