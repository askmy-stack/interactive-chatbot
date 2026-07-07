"""
FastAPI endpoint tests.

Uses FastAPI's synchronous TestClient. The agent is NOT initialised
(no real LLM calls) — only structural endpoint behaviour is tested.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Return a TestClient with the agent's astream_response mocked out."""
    from backend.main import app, session_histories
    session_histories.clear()

    async def _fake_stream(user_input, session_id, chat_history):
        yield "Hello "
        yield "from "
        yield "A.S.K.!"

    with patch("backend.main.astream_response", new=_fake_stream):
        # Pre-import so the patch is in place when TestClient starts
        import backend.agent  # noqa: F401
        with TestClient(app) as c:
            yield c

    session_histories.clear()


# ── /health ────────────────────────────────────────────────────────────────────

def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "model" in data
    assert "provider" in data


# ── /chat/stream ───────────────────────────────────────────────────────────────

def test_chat_stream_returns_text(client):
    resp = client.post(
        "/chat/stream",
        json={"message": "Hello A.S.K.", "session_id": "test-session"},
    )
    assert resp.status_code == 200
    assert "A.S.K." in resp.text
    assert "data:" in resp.text


def test_chat_sync_endpoint(client):
    resp = client.post(
        "/chat",
        json={"message": "Hello sync", "session_id": "sync-session"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "sync-session"
    assert data["input_channel"] == "text"
    assert data["output_channel"] == "text"
    assert "response" in data


def test_voice_chat_envelope(client):
    resp = client.post(
        "/voice/chat",
        json={"transcript": "hello voice", "session_id": "voice-session"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == "voice-session"
    assert data["input_channel"] == "voice"
    assert data["output_channel"] == "voice"
    assert data["transcript"] == "hello voice"
    assert "tts" in data


def test_chat_stream_rejects_empty_message(client):
    resp = client.post(
        "/chat/stream",
        json={"message": "   ", "session_id": "test-session"},
    )
    assert resp.status_code == 400


def test_chat_stream_builds_session_history(client):
    from backend.main import session_histories

    client.post("/chat/stream", json={"message": "Hi", "session_id": "hist-test"})
    assert "hist-test" in session_histories
    assert len(session_histories["hist-test"]) == 2  # HumanMessage + AIMessage


# ── /chat/{session_id} DELETE ──────────────────────────────────────────────────

def test_clear_session(client):
    from backend.main import session_histories

    session_histories["to-clear"] = ["msg1", "msg2"]
    resp = client.delete("/chat/to-clear")
    assert resp.status_code == 200
    assert "to-clear" not in session_histories


def test_clear_nonexistent_session(client):
    """Clearing a session that doesn't exist should not raise."""
    resp = client.delete("/chat/does-not-exist")
    assert resp.status_code == 200


# ── /chat/{session_id}/history ────────────────────────────────────────────────

def test_get_history_empty(client):
    resp = client.get("/chat/empty-session/history")
    assert resp.status_code == 200
    data = resp.json()
    assert data["turn_count"] == 0
    assert data["messages"] == []


def test_get_history_after_chat(client):
    client.post("/chat/stream", json={"message": "Hello", "session_id": "hist-check"})
    resp = client.get("/chat/hist-check/history")
    data = resp.json()
    assert data["turn_count"] == 1
    assert data["messages"][0]["role"] == "human"
    assert data["messages"][1]["role"] == "ai"
