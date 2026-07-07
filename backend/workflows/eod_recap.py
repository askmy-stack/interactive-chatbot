from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from backend.memory_graph import EntityType, MemoryGraph
from backend.tools.calendar_apple import get_today_schedule


def _tz() -> ZoneInfo:
    return ZoneInfo("America/New_York")


def build_eod_recap(memory_graph: MemoryGraph) -> str:
    """Summarize the day: schedule replay, goals touched, open commitments."""
    schedule = get_today_schedule.invoke({})
    goals = memory_graph.query_entities(EntityType.GOAL, limit=5)
    projects = memory_graph.query_entities(EntityType.PROJECT, limit=5)
    commitments = memory_graph.query("commitment.")

    lines = [
        "End-of-day recap",
        "",
        "What happened today:",
        schedule,
        "",
    ]
    if projects:
        lines.append("Project focus:")
        for p in projects:
            lines.append(f"- {p.name}: {p.attributes or 'active'}")
        lines.append("")
    if goals:
        lines.append("Goal progress check:")
        for g in goals:
            lines.append(f"- {g.name}")
        lines.append("")
    if commitments:
        lines.append("Still open:")
        for c in commitments[:5]:
            lines.append(f"- {c.value}")
    else:
        lines.append("No open commitments tracked.")
    lines.append("")
    lines.append("Nice work today. Rest up.")
    return "\n".join(lines)


def build_next_day_prep(memory_graph: MemoryGraph) -> str:
    """Prepare for tomorrow: first events, routines, and suggested focus blocks."""
    now = datetime.now(_tz())
    tomorrow = now.date() + timedelta(days=1)
    start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=_tz())
    end = start + timedelta(days=1)

    from backend.tools.calendar_apple import _provider

    events = _provider().get_events(start, end)
    routines = memory_graph.query_entities(EntityType.ROUTINE, limit=5)
    people = memory_graph.query_entities(EntityType.PERSON, limit=5)

    lines = ["Next-day prep", "", f"Date: {tomorrow.strftime('%A, %B %d')}", ""]
    if events:
        lines.append("Tomorrow's calendar:")
        for ev in events[:8]:
            lines.append(f"- {ev.start.strftime('%I:%M %p')}: {ev.title}")
    else:
        lines.append("No events on tomorrow's calendar yet.")
    lines.append("")
    if routines:
        lines.append("Morning routines:")
        for r in routines:
            lines.append(f"- {r.name}")
        lines.append("")
    if people:
        lines.append("People to connect with:")
        for p in people[:3]:
            lines.append(f"- {p.name}")
        lines.append("")
    lines.append("Suggested focus: block 90 minutes for your top priority before noon.")
    return "\n".join(lines)
