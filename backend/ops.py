from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from backend.config import settings


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
