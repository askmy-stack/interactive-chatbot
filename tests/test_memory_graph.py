from __future__ import annotations

from backend.memory_graph import Fact, MemoryGraph


def test_memory_graph_insert_and_query(tmp_path):
 graph = MemoryGraph(str(tmp_path / "graph.db"))
 graph.add_fact(Fact(key="commitment.user", value="I will submit report", source="s1"))
 rows = graph.query("commitment.")
 assert rows
 assert "submit report" in rows[0].value

