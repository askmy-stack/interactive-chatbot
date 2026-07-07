from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from backend.main import app, session_histories

    session_histories.clear()

    async def _fake_stream(user_input, session_id, chat_history):
        yield "voice ok"

    with patch("backend.main.astream_response", new=_fake_stream):
        with TestClient(app) as c:
            yield c


def test_voice_tts_endpoint(client):
    resp = client.post("/voice/tts", json={"text": "hello"})
    assert resp.status_code == 200
    data = resp.json()
    assert "audio_base64" in data
    assert "tts_available" in data


def test_voice_tts_status(client):
    resp = client.get("/voice/tts/status")
    assert resp.status_code == 200
    assert "tts_available" in resp.json()


def test_health_includes_deployment_mode(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "deployment_mode" in data
    assert "tts" in data


def test_morning_brief_endpoint(client):
    resp = client.get("/brief/morning")
    assert resp.status_code == 200
    assert "brief" in resp.json()


def test_eod_and_next_day_briefs(client):
    eod = client.get("/brief/eod")
    nxt = client.get("/brief/next-day")
    assert eod.status_code == 200
    assert nxt.status_code == 200


def test_reminders_brief(client):
    resp = client.get("/brief/reminders")
    assert resp.status_code == 200
    assert "Proactive reminders" in resp.json()["brief"]


def test_stt_status_endpoint(client):
    resp = client.get("/voice/stt/status")
    assert resp.status_code == 200
    assert "backends" in resp.json()


def test_stt_transcribe_browser_fallback(client):
    resp = client.post(
        "/voice/stt/transcribe",
        json={"audio_base64": "", "browser_transcript": "hello from browser"},
    )
    assert resp.status_code == 200
    assert resp.json()["text"] == "hello from browser"


def test_stt_transcribe_empty(client):
    resp = client.post("/voice/stt/transcribe", json={"audio_base64": ""})
    assert resp.status_code == 200
    assert resp.json()["backend"] == "unavailable"


def test_provider_health_endpoint(client):
    with patch("backend.providers.health.httpx.get") as mock_get:
        mock_get.return_value.status_code = 200
        resp = client.get("/health/providers")
    assert resp.status_code == 200
    body = resp.json()
    assert "providers" in body
    assert "active_provider" in body


def test_ops_restore_endpoint(client, tmp_path):
    src = tmp_path / "source.db"
    dst = tmp_path / "target.db"
    src.write_text("backup-data", encoding="utf-8")
    resp = client.post(
        "/ops/restore",
        json={"backup_path": str(src), "target_path": str(dst)},
    )
    assert resp.status_code == 200
    assert dst.read_text(encoding="utf-8") == "backup-data"
