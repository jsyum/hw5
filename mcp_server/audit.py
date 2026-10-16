"""Append-only audit trail at output/audit_trail.json.

The file is always a valid JSON array. Appending only removes the closing
bracket and writes the new entry plus a new closing bracket; earlier entries
are never rewritten, reordered, or deleted, and nothing resets the file.
An exclusive file lock makes concurrent appends (backend run, approval CLI)
safe.
"""

from __future__ import annotations

import fcntl
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = Path(os.environ.get("CAMPUS_CUSTOMS_AUDIT", PROJECT_ROOT / "output" / "audit_trail.json"))
MAX_FIELD_CHARS = 4000


def _clip(value: Any) -> Any:
    if isinstance(value, str) and len(value) > MAX_FIELD_CHARS:
        return value[:MAX_FIELD_CHARS] + f"... [truncated {len(value) - MAX_FIELD_CHARS} chars]"
    if isinstance(value, dict):
        return {k: _clip(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clip(v) for v in value]
    return value


def append(event: str, **fields: Any) -> dict[str, Any]:
    """Append one entry. Returns the entry as written."""
    entry = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "event": event, **_clip(fields)}
    line = json.dumps(entry, default=str, ensure_ascii=False)
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_PATH, "a+b") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            if size == 0:
                f.write(f"[\n{line}\n]\n".encode())
                return entry
            # Find the final ']' and append before it.
            pos = size
            f.seek(0)
            tail_start = max(0, size - 64)
            f.seek(tail_start)
            tail = f.read()
            idx = tail.rfind(b"]")
            if idx < 0:
                raise RuntimeError(f"{AUDIT_PATH} is not a JSON array; refusing to modify it")
            pos = tail_start + idx
            f.truncate(pos)
            f.seek(pos)
            f.write(f",\n{line}\n]\n".encode())
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    return entry
