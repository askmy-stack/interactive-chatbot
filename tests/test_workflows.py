from __future__ import annotations

from backend.memory_graph import Entity, EntityType, MemoryGraph
from backend.workflows.eod_recap import build_eod_recap, build_next_day_prep
from backend.workflows.reminders import build_proactive_reminders


def test_eod_recap_contains_heading(tmp_path, monkeypatch):
    graph = MemoryGraph(str(tmp_path / "graph.db"))
    graph.add_entity(Entity(EntityType.GOAL, "Ship", "v1", "test"))
    text = build_eod_recap(graph)
    assert "End-of-day recap" in text


def test_next_day_prep_contains_date(tmp_path):
    graph = MemoryGraph(str(tmp_path / "graph.db"))
    text = build_next_day_prep(graph)
    assert "Next-day prep" in text


def test_proactive_reminders(monkeypatch):
    from backend.tools import calendar_apple

    class FakeProvider:
        def get_events(self, start, end):
            return []

    monkeypatch.setattr(calendar_apple, "_provider", lambda: FakeProvider())
    text = build_proactive_reminders()
    assert "Proactive reminders" in text
