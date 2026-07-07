from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from backend.calendar_approval import approval_store
from backend.integrations.calendar.apple_calendar import AppleCalendarProvider
from backend.integrations.calendar.base import CalendarEventInput


def _tz() -> ZoneInfo:
    return ZoneInfo("America/New_York")


def _provider() -> AppleCalendarProvider:
    return AppleCalendarProvider()


def _require_approval(approval_token: str, action: str) -> str | None:
    if not approval_token:
        return (
            f"Calendar {action} requires explicit user approval. "
            "Call POST /calendar/approve with action name, then retry with approval_token."
        )
    if not approval_store.consume(approval_token, action):
        return "Invalid or expired approval token. Request a new approval token."
    return None


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


@tool
def create_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    calendar: str = "Calendar",
    approval_token: str = "",
) -> str:
    """Create a calendar event. Requires approval_token from POST /calendar/approve."""
    err = _require_approval(approval_token, "create_event")
    if err:
        return err
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    event_id = _provider().create_event(
        CalendarEventInput(title=title, start=start, end=end, calendar=calendar)
    )
    return f"Created event '{title}' (id={event_id})."


@tool
def update_calendar_event(
    event_id: str,
    title: str,
    start_iso: str,
    end_iso: str,
    approval_token: str = "",
) -> str:
    """Update a calendar event. Requires approval_token from POST /calendar/approve."""
    err = _require_approval(approval_token, "update_event")
    if err:
        return err
    start = datetime.fromisoformat(start_iso)
    end = datetime.fromisoformat(end_iso)
    ok = _provider().update_event(
        event_id,
        CalendarEventInput(title=title, start=start, end=end),
    )
    if not ok:
        return f"Failed to update event {event_id}."
    return f"Updated event {event_id} to '{title}'."
