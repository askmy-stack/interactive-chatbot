from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.integrations.calendar.base import CalendarEvent


def test_today_schedule_format(monkeypatch):
 from backend.tools import calendar_apple

 class FakeProvider:
  def get_events(self, start, end):
   return [
    CalendarEvent(
     start=datetime.now(ZoneInfo("America/New_York")).replace(hour=10, minute=0, second=0, microsecond=0),
     end=datetime.now(ZoneInfo("America/New_York")).replace(hour=11, minute=0, second=0, microsecond=0),
     title="Standup",
    )
   ]

 monkeypatch.setattr(calendar_apple, "_provider", lambda: FakeProvider())
 out = calendar_apple.get_today_schedule.invoke({})
 assert "Today's schedule" in out
 assert "Standup" in out


def test_next_event_empty(monkeypatch):
 from backend.tools import calendar_apple

 class EmptyProvider:
  def get_events(self, start, end):
   return []

 monkeypatch.setattr(calendar_apple, "_provider", lambda: EmptyProvider())
 out = calendar_apple.get_next_event.invoke({})
 assert "No upcoming events" in out

