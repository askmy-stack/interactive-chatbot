from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


class EntityType(StrEnum):
    PERSON = "person"
    PROJECT = "project"
    GOAL = "goal"
    ROUTINE = "routine"
    FACT = "fact"


@dataclass
class Fact:
    key: str
    value: str
    source: str


@dataclass
class Entity:
    entity_type: EntityType
    name: str
    attributes: str
    source: str


class MemoryGraph:
    def __init__(self, path: str = "./memory_graph.db") -> None:
        self.path = Path(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS facts ("
            "key TEXT, value TEXT, source TEXT, "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS entities ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "entity_type TEXT NOT NULL, "
            "name TEXT NOT NULL, "
            "attributes TEXT DEFAULT '', "
            "source TEXT DEFAULT '', "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS entity_links ("
            "from_id INTEGER, to_id INTEGER, relation TEXT, "
            "created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
        )
        self.conn.commit()

    def add_fact(self, fact: Fact) -> None:
        self.conn.execute(
            "INSERT INTO facts(key, value, source) VALUES (?, ?, ?)",
            (fact.key, fact.value, fact.source),
        )
        self.conn.commit()

    def query(self, key_prefix: str, limit: int = 10) -> list[Fact]:
        rows = self.conn.execute(
            "SELECT key, value, source FROM facts WHERE key LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (f"{key_prefix}%", limit),
        ).fetchall()
        return [Fact(key=r[0], value=r[1], source=r[2]) for r in rows]

    def add_entity(self, entity: Entity) -> int:
        cur = self.conn.execute(
            "INSERT INTO entities(entity_type, name, attributes, source) VALUES (?, ?, ?, ?)",
            (entity.entity_type.value, entity.name, entity.attributes, entity.source),
        )
        self.conn.commit()
        return int(cur.lastrowid or 0)

    def query_entities(
        self,
        entity_type: EntityType | None = None,
        name_prefix: str = "",
        limit: int = 20,
    ) -> list[Entity]:
        clauses = ["1=1"]
        params: list[str | int] = []
        if entity_type:
            clauses.append("entity_type = ?")
            params.append(entity_type.value)
        if name_prefix:
            clauses.append("name LIKE ?")
            params.append(f"{name_prefix}%")
        params.append(limit)
        sql = (
            f"SELECT entity_type, name, attributes, source FROM entities "
            f"WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT ?"
        )
        rows = self.conn.execute(sql, params).fetchall()
        return [
            Entity(
                entity_type=EntityType(r[0]),
                name=r[1],
                attributes=r[2],
                source=r[3],
            )
            for r in rows
        ]

    def link_entities(self, from_id: int, to_id: int, relation: str) -> None:
        self.conn.execute(
            "INSERT INTO entity_links(from_id, to_id, relation) VALUES (?, ?, ?)",
            (from_id, to_id, relation),
        )
        self.conn.commit()

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for et in EntityType:
            if et == EntityType.FACT:
                continue
            row = self.conn.execute(
                "SELECT COUNT(*) FROM entities WHERE entity_type = ?",
                (et.value,),
            ).fetchone()
            counts[et.value] = int(row[0]) if row else 0
        fact_row = self.conn.execute("SELECT COUNT(*) FROM facts").fetchone()
        counts["fact"] = int(fact_row[0]) if fact_row else 0
        return counts
