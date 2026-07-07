from __future__ import annotations

from backend.memory_graph import EntityType, MemoryGraph
from backend.tools.calendar_apple import get_today_schedule


def build_morning_brief(memory_graph: MemoryGraph) -> str:
    schedule = get_today_schedule.invoke({})
    commitments = memory_graph.query("commitment.")
    goals = memory_graph.query_entities(EntityType.GOAL, limit=5)
    routines = memory_graph.query_entities(EntityType.ROUTINE, limit=3)
    lines = ["Good morning. Here is your daily brief:", "", schedule, ""]
    if goals:
        lines.append("Active goals:")
        for item in goals:
            lines.append(f"- {item.name}: {item.attributes or 'in progress'}")
        lines.append("")
    if routines:
        lines.append("Today's routines:")
        for item in routines:
            lines.append(f"- {item.name}")
        lines.append("")
    if commitments:
        lines.append("Open commitments:")
        for fact in commitments[:5]:
            lines.append(f"- {fact.value}")
    else:
        lines.append("No tracked commitments yet.")
    return "\n".join(lines)
