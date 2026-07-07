"""A.S.K. Python SDK — minimal client for external integrations."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import httpx


class AskClient:
  def __init__(
      self,
      base_url: str = "http://localhost:8000",
      api_key: str | None = None,
      client: str = "external-app",
  ) -> None:
      self.base_url = base_url.rstrip("/")
      self.api_key = api_key
      self.client = client

  def _headers(self) -> dict[str, str]:
      headers = {"Content-Type": "application/json", "X-ASK-Client": self.client}
      if self.api_key:
          headers["Authorization"] = f"Bearer {self.api_key}"
      return headers

  def health(self) -> dict[str, Any]:
      with httpx.Client() as http:
          resp = http.get(f"{self.base_url}/health", headers=self._headers())
          resp.raise_for_status()
          return resp.json()

  def chat(self, message: str, session_id: str = "default") -> dict[str, Any]:
      with httpx.Client() as http:
          resp = http.post(
              f"{self.base_url}/chat",
              headers=self._headers(),
              json={
                  "message": message,
                  "session_id": session_id,
                  "input_channel": "text",
                  "output_channel": "text",
              },
          )
          resp.raise_for_status()
          return resp.json()

  def chat_stream(self, message: str, session_id: str = "default") -> Iterator[dict[str, Any]]:
      with httpx.Client() as http:
          with http.stream(
              "POST",
              f"{self.base_url}/chat/stream",
              headers=self._headers(),
              json={
                  "message": message,
                  "session_id": session_id,
                  "input_channel": "text",
                  "output_channel": "text",
              },
          ) as resp:
              resp.raise_for_status()
              for line in resp.iter_lines():
                  if line.startswith("data: "):
                      import json

                      yield json.loads(line[6:])

  def voice_chat(self, transcript: str, session_id: str = "default") -> dict[str, Any]:
      with httpx.Client() as http:
          resp = http.post(
              f"{self.base_url}/voice/chat",
              headers=self._headers(),
              json={
                  "transcript": transcript,
                  "session_id": session_id,
                  "input_channel": "voice",
                  "output_channel": "voice",
              },
          )
          resp.raise_for_status()
          return resp.json()

  def morning_brief(self) -> str:
      with httpx.Client() as http:
          resp = http.get(f"{self.base_url}/brief/morning", headers=self._headers())
          return resp.json()["brief"]

  def calendar_approve(self, action: str = "create_event") -> dict[str, Any]:
      with httpx.Client() as http:
          resp = http.post(
              f"{self.base_url}/calendar/approve",
              headers=self._headers(),
              json={"action": action},
          )
          return resp.json()

  def clear_session(self, session_id: str) -> None:
      with httpx.Client() as http:
          http.delete(f"{self.base_url}/chat/{session_id}", headers=self._headers())
