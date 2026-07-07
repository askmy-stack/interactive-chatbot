from __future__ import annotations

from pathlib import Path

from backend.ops import backup_file, list_backups, restore_file


def test_backup_and_restore_roundtrip(tmp_path, monkeypatch):
    from backend.config import Settings

    backup_dir = tmp_path / "backups"
    monkeypatch.setattr("backend.ops.settings", Settings(backup_dir=str(backup_dir)))

    src = tmp_path / "memory_graph.db"
    src.write_text("graph-data", encoding="utf-8")
    backup_path = backup_file(str(src))
    assert backup_path
    assert Path(backup_path).exists()

    dst = tmp_path / "restored.db"
    restored = restore_file(backup_path, str(dst))
    assert restored == str(dst)
    assert dst.read_text(encoding="utf-8") == "graph-data"
    assert backup_path in list_backups()
