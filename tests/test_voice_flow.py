from __future__ import annotations

from fastapi.testclient import TestClient
from unittest.mock import patch

import pytest


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
 assert "audio_base64" in resp.json()


def test_morning_brief_endpoint(client):
 resp = client.get("/brief/morning")
 assert resp.status_code == 200
 assert "brief" in resp.json()

