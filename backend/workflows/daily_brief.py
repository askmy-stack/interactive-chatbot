from __future__ import annotations

from backend.memory_graph import MemoryGraph
from backend.tools.calendar_apple import get_today_schedule


def build_morning_brief(memory_graph: MemoryGraph) -> str:
    schedule = get_today_schedule.invoke({})
    commitments = memory_graph.query("commitment.")
    lines = ["Good morning. Here is your daily brief:", "", schedule, ""]
    if commitments:
        lines.append("Open commitments:")
        for item in commitments[:5]:
            lines.append(f"- {item.value}")
    else:
        lines.append("No tracked commitments yet.")
    return "\n".join(lines)
