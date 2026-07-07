from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from backend.calendar_approval import CalendarApprovalStore
from backend.integrations.calendar.base import CalendarEvent, CalendarEventInput


def test_today_schedule_format(monkeypatch):
    from backend.tools import calendar_apple

    class FakeProvider:
        def get_events(self, start, end):
            return [
                CalendarEvent(
                    start=datetime.now(ZoneInfo("America/New_York")).replace(
                        hour=10, minute=0, second=0, microsecond=0
                    ),
                    end=datetime.now(ZoneInfo("America/New_York")).replace(
                        hour=11, minute=0, second=0, microsecond=0
                    ),
                    title="Standup",
                )
            ]

        def create_event(self, event: CalendarEventInput) -> str:
            return "evt-1"

        def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
            return True

    monkeypatch.setattr(calendar_apple, "_provider", lambda: FakeProvider())
    out = calendar_apple.get_today_schedule.invoke({})
    assert "Today's schedule" in out
    assert "Standup" in out


def test_next_event_empty(monkeypatch):
    from backend.tools import calendar_apple

    class EmptyProvider:
        def get_events(self, start, end):
            return []

        def create_event(self, event: CalendarEventInput) -> str:
            return "evt-1"

        def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
            return True

    monkeypatch.setattr(calendar_apple, "_provider", lambda: EmptyProvider())
    out = calendar_apple.get_next_event.invoke({})
    assert "No upcoming events" in out


def test_create_event_requires_approval(monkeypatch):
    from backend.tools import calendar_apple

    class FakeProvider:
        def get_events(self, start, end):
            return []

        def create_event(self, event: CalendarEventInput) -> str:
            return "evt-99"

        def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
            return True

    monkeypatch.setattr(calendar_apple, "_provider", lambda: FakeProvider())
    out = calendar_apple.create_calendar_event.invoke(
        {
            "title": "Focus",
            "start_iso": "2026-07-08T10:00:00",
            "end_iso": "2026-07-08T11:00:00",
        }
    )
    assert "approval" in out.lower()


def test_create_event_with_approval_token(monkeypatch):
    from backend.tools import calendar_apple

    store = CalendarApprovalStore()
    grant = store.request_approval("create_event")
    monkeypatch.setattr(calendar_apple, "approval_store", store)

    class FakeProvider:
        def get_events(self, start, end):
            return []

        def create_event(self, event: CalendarEventInput) -> str:
            return "evt-99"

        def update_event(self, event_id: str, event: CalendarEventInput) -> bool:
            return True

    monkeypatch.setattr(calendar_apple, "_provider", lambda: FakeProvider())
    out = calendar_apple.create_calendar_event.invoke(
        {
            "title": "Focus",
            "start_iso": "2026-07-08T10:00:00",
            "end_iso": "2026-07-08T11:00:00",
            "approval_token": grant.token,
        }
    )
    assert "Created event" in out


def test_calendar_approve_endpoint():
    from fastapi.testclient import TestClient

    from backend.main import app

    with TestClient(app) as client:
        resp = client.post("/calendar/approve", json={"action": "create_event"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "create_event"
    assert data["approval_token"]
