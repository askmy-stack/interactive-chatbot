from __future__ import annotations

from backend.memory_graph import Entity, EntityType, Fact, MemoryGraph


def test_memory_graph_insert_and_query(tmp_path):
    graph = MemoryGraph(str(tmp_path / "graph.db"))
    graph.add_fact(Fact(key="commitment.user", value="I will submit report", source="s1"))
    rows = graph.query("commitment.")
    assert rows
    assert "submit report" in rows[0].value


def test_memory_graph_entities(tmp_path):
    graph = MemoryGraph(str(tmp_path / "graph.db"))
    pid = graph.add_entity(
        Entity(entity_type=EntityType.PERSON, name="Alex", attributes="teammate", source="test")
    )
    gid = graph.add_entity(
        Entity(entity_type=EntityType.GOAL, name="Ship v1", attributes="Q3", source="test")
    )
    graph.link_entities(pid, gid, "supports")
    people = graph.query_entities(EntityType.PERSON)
    assert people and people[0].name == "Alex"
    summary = graph.summary()
    assert summary["person"] >= 1
    assert summary["goal"] >= 1
