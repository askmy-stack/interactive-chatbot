from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Fact:
 key: str
 value: str
 source: str


class MemoryGraph:
 def __init__(self, path: str = "./memory_graph.db") -> None:
  self.path = Path(path)
  self.conn = sqlite3.connect(self.path, check_same_thread=False)
  self.conn.execute(
   "CREATE TABLE IF NOT EXISTS facts (key TEXT, value TEXT, source TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)"
  )
  self.conn.commit()

 def add_fact(self, fact: Fact) -> None:
  self.conn.execute("INSERT INTO facts(key, value, source) VALUES (?, ?, ?)", (fact.key, fact.value, fact.source))
  self.conn.commit()

 def query(self, key_prefix: str, limit: int = 10) -> list[Fact]:
  rows = self.conn.execute(
   "SELECT key, value, source FROM facts WHERE key LIKE ? ORDER BY created_at DESC LIMIT ?",
   (f"{key_prefix}%", limit),
  ).fetchall()
  return [Fact(key=r[0], value=r[1], source=r[2]) for r in rows]

