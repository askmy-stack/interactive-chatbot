from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.tools.calendar_apple import _provider, get_free_time_blocks


def _tz() -> ZoneInfo:
    return ZoneInfo("America/New_York")


def build_proactive_reminders() -> str:
    """Remind before upcoming meetings and suggest free-block usage."""
    now = datetime.now(_tz())
    horizon = now + timedelta(hours=12)
    events = _provider().get_events(now, horizon)
    upcoming = [ev for ev in events if ev.start > now]

    lines = ["Proactive reminders", ""]
    if not upcoming:
        lines.append("No meetings in the next 12 hours.")
    else:
        for ev in upcoming[:5]:
            minutes = int((ev.start - now).total_seconds() // 60)
            if minutes <= 15:
                lines.append(f"⏰ Starting soon ({minutes}m): {ev.title} at {ev.start.strftime('%I:%M %p')}")
            elif minutes <= 60:
                lines.append(f"📅 In {minutes}m: {ev.title}")
            else:
                lines.append(f"📅 Later today: {ev.title} at {ev.start.strftime('%I:%M %p')}")

    lines.append("")
    free = get_free_time_blocks.invoke({"hours": 5})
    lines.append("Free-block suggestions:")
    lines.append(free)
    if "Free blocks today" in free:
        lines.append("")
        lines.append("Tip: use a 25-minute block for email and a 50-minute block for deep work.")
    return "\n".join(lines)
