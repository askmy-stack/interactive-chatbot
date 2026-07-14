from __future__ import annotations

from pathlib import Path

from backend.ops import (
    backup_file,
    is_allowed_backup_source,
    is_allowed_restore_target,
    list_backups,
    restore_file,
)


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


def test_is_allowed_restore_target_accepts_managed_paths():
    assert is_allowed_restore_target("./chroma_db/chroma.sqlite3")
    assert is_allowed_restore_target("./memory_graph.db")


def test_is_allowed_restore_target_rejects_arbitrary_paths():
    assert not is_allowed_restore_target("/etc/passwd")
    assert not is_allowed_restore_target("../../etc/passwd")
    assert not is_allowed_restore_target("./backend/config.py")


def test_is_allowed_backup_source_requires_backup_dir(tmp_path, monkeypatch):
    from backend.config import Settings

    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    monkeypatch.setattr("backend.ops.settings", Settings(backup_dir=str(backup_dir)))

    assert is_allowed_backup_source(str(backup_dir / "memory_graph.db.20240101.bak"))
    assert not is_allowed_backup_source("/etc/passwd")
    assert not is_allowed_backup_source(str(tmp_path / "outside.bak"))
