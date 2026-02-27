"""Tests for WISDOM Body module — API endpoints, code playground."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient

import wisdom.body.api as api_module
from wisdom.body.api import app
from wisdom.body.components.code_playground import _safe_exec


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


@pytest.fixture(autouse=True)
def reset_wisdom():
    """Reset shared WISDOM instance between tests to avoid state leaks."""
    api_module._wisdom = None
    yield
    api_module._wisdom = None


@pytest.fixture
def client():
    return TestClient(app)


def _unique_id() -> str:
    return f"test_{uuid.uuid4().hex[:8]}"


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
        response = client.get(f"/api/v1/profile/{_unique_id()}")
        assert response.status_code == 404

    def test_create_and_get_profile(self, client):
        uid = _unique_id()
        # Create
        response = client.post(
            "/api/v1/profile",
            json={"user_id": uid, "name": "Test", "language": "en"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"

        # Get
        response = client.get(f"/api/v1/profile/{uid}")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_update_profile(self, client):
        uid = _unique_id()
        client.post(
            "/api/v1/profile",
            json={"user_id": uid, "name": "Old"},
        )
        response = client.put(
            f"/api/v1/profile/{uid}",
            json={"name": "New Name", "skill_level": 5.0},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    def test_delete_profile(self, client):
        uid = _unique_id()
        client.post(
            "/api/v1/profile",
            json={"user_id": uid},
        )
        response = client.delete(f"/api/v1/profile/{uid}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify deleted
        response = client.get(f"/api/v1/profile/{uid}")
        assert response.status_code == 404

    @pytest.mark.skipif(
        not _llm_available(),
        reason="Requires a running LLM (Ollama with model or GOOGLE_API_KEY)",
    )
    def test_chat_creates_profile(self, client):
        response = client.post(
            "/api/v1/chat",
            json={"user_id": _unique_id(), "message": "Hello!"},
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

    def test_feedback_with_category(self, client):
        response = client.post(
            "/api/v1/feedback",
            json={"rating": 4, "comment": "Nice UI", "category": "ui"},
        )
        assert response.status_code == 200

    def test_feedback_stats(self, client):
        client.post("/api/v1/feedback", json={"rating": 5})
        response = client.get("/api/v1/feedback/stats")
        assert response.status_code == 200
        assert "total" in response.json()


class TestExportEndpoint:
    def test_export_user_data(self, client):
        uid = _unique_id()
        client.post(
            "/api/v1/profile",
            json={"user_id": uid, "name": "ExportTest"},
        )
        response = client.get(f"/api/v1/profile/{uid}/export")
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "conversation_count" in data
        assert "goals" in data
        assert "badges" in data
        assert "learning_progress" in data

    def test_export_nonexistent(self, client):
        response = client.get(f"/api/v1/profile/{_unique_id()}/export")
        assert response.status_code == 404


class TestLearningEndpoints:
    def test_assessment_start(self, client):
        response = client.post("/api/v1/assessment/start")
        assert response.status_code == 200
        data = response.json()
        assert "question" in data

    def test_learning_path(self, client):
        uid = _unique_id()
        client.post(
            "/api/v1/profile",
            json={"user_id": uid},
        )
        response = client.get(f"/api/v1/learning-path/{uid}")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "next_lesson" in data


class TestOfflineMode:
    def test_llm_provider_is_offline(self):
        from unittest.mock import MagicMock
        from wisdom.core.llm_provider import LLMProvider
        config = MagicMock()
        config.ollama_base_url = "http://localhost:99999"
        config.has_gemini = False
        config.google_api_key = ""
        config.ollama_model = "test"
        provider = LLMProvider(config)
        assert provider.is_offline()
        assert not provider.is_local()


class TestCodePlayground:
    def test_safe_exec_print(self):
        stdout, stderr = _safe_exec('print("hello")')
        assert "hello" in stdout
        assert stderr == ""

    def test_safe_exec_loop(self):
        stdout, stderr = _safe_exec("for i in range(3): print(i)")
        assert "0" in stdout
        assert "2" in stdout

    def test_safe_exec_error(self):
        stdout, stderr = _safe_exec("1/0")
        assert "ZeroDivisionError" in stderr

    def test_safe_exec_no_import(self):
        stdout, stderr = _safe_exec("import os")
        assert "NameError" in stderr or "ImportError" in stderr or stderr != ""

    def test_safe_exec_list_comprehension(self):
        stdout, stderr = _safe_exec("print([x**2 for x in range(5)])")
        assert "[0, 1, 4, 9, 16]" in stdout

    def test_safe_exec_function(self):
        code = "def add(a, b): return a + b\nprint(add(2, 3))"
        stdout, stderr = _safe_exec(code)
        assert "5" in stdout
