from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from backend.config import settings

# Fixed set of files /ops/backup manages. /ops/restore only allows restoring
# into these paths, so a caller can't use it to overwrite arbitrary files.
MANAGED_RESTORE_TARGETS = frozenset({"./chroma_db/chroma.sqlite3", "./memory_graph.db"})


def _is_within(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def is_allowed_restore_target(target_path: str) -> bool:
    """Only allow restoring into the fixed set of files ops/backup manages."""
    resolved = Path(target_path).resolve()
    return resolved in {Path(p).resolve() for p in MANAGED_RESTORE_TARGETS}


def is_allowed_backup_source(backup_path: str) -> bool:
    """Only allow restoring from a backup file inside the configured backup dir."""
    return _is_within(Path(backup_path), Path(settings.backup_dir))


def redact_text(text: str) -> str:
    if not settings.redact_pii:
        return text
    text = re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[redacted-email]",
        text,
    )
    text = re.sub(r"\b\d{3}[-.\s]?\d{2,4}[-.\s]?\d{4}\b", "[redacted-number]", text)
    return text


def backup_file(path: str) -> str:
    src = Path(path)
    if not src.exists():
        return ""
    dst_dir = Path(settings.backup_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = dst_dir / f"{src.name}.{stamp}.bak"
    shutil.copy2(src, dst)
    return str(dst)


def restore_file(backup_path: str, target_path: str) -> str:
    """Restore a backup file to its original location. Returns target path or empty on failure."""
    src = Path(backup_path)
    dst = Path(target_path)
    if not src.exists():
        return ""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        pre_restore = backup_file(str(dst))
        if pre_restore:
            pass  # safety snapshot before overwrite
    shutil.copy2(src, dst)
    return str(dst)


def list_backups(pattern: str = "*.bak") -> list[str]:
    backup_dir = Path(settings.backup_dir)
    if not backup_dir.exists():
        return []
    return sorted(str(p) for p in backup_dir.glob(pattern))
