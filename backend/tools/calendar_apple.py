from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from backend.integrations.calendar.apple_calendar import AppleCalendarProvider


def _tz() -> ZoneInfo:
 return ZoneInfo("America/New_York")


def _provider() -> AppleCalendarProvider:
 return AppleCalendarProvider()


@tool
def get_today_schedule() -> str:
 """Return today's Apple Calendar schedule."""
 now = datetime.now(_tz())
 start = datetime.combine(now.date(), time.min, tzinfo=_tz())
 end = start + timedelta(days=1)
 events = _provider().get_events(start, end)
 if not events:
  return "No calendar events scheduled for today."
 lines = ["Today's schedule:"]
 for ev in events:
  lines.append(f"- {ev.start.strftime('%I:%M %p')} to {ev.end.strftime('%I:%M %p')}: {ev.title}")
 return "\n".join(lines)


@tool
def get_next_event() -> str:
 """Return the next upcoming Apple Calendar event."""
 now = datetime.now(_tz())
 events = _provider().get_events(now, now + timedelta(days=7))
 upcoming = [ev for ev in events if ev.end > now]
 if not upcoming:
  return "No upcoming events found in the next 7 days."
 ev = upcoming[0]
 return f"Next event: {ev.title} at {ev.start.strftime('%a %b %d, %I:%M %p')}."


@tool
def get_free_time_blocks(hours: int = 10) -> str:
 """Return free-time windows remaining today."""
 now = datetime.now(_tz())
 start_day = datetime.combine(now.date(), time(hour=8), tzinfo=_tz())
 end_day = datetime.combine(now.date(), time(hour=18), tzinfo=_tz())
 events = _provider().get_events(start_day, end_day)
 cursor = max(now, start_day)
 free: list[tuple[datetime, datetime]] = []
 for ev in events:
  if ev.start > cursor:
   free.append((cursor, ev.start))
  if ev.end > cursor:
   cursor = ev.end
 if cursor < end_day:
  free.append((cursor, end_day))
 if not free:
  return "No free time blocks left today."
 lines = ["Free blocks today:"]
 for s, e in free:
  lines.append(f"- {s.strftime('%I:%M %p')} to {e.strftime('%I:%M %p')}")
 return "\n".join(lines[: hours + 1])

