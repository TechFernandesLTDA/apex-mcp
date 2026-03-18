"""Operation audit trail for apex-mcp.

Logs all tool invocations to a JSON Lines file for debugging and compliance.
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

_log = logging.getLogger("apex_mcp.audit")

# Default audit log location
_AUDIT_DIR = Path(os.environ.get("APEX_MCP_AUDIT_DIR", Path.home() / ".apex_mcp"))
_AUDIT_FILE = _AUDIT_DIR / "audit.jsonl"


class AuditLog:
    """Append-only audit log for tool operations."""

    _instance: AuditLog | None = None

    def __init__(self, path: Path = _AUDIT_FILE):
        self._path = path
        self._enabled = True
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            _log.warning("Cannot create audit directory %s, disabling audit", path.parent)
            self._enabled = False

    @classmethod
    def get(cls) -> AuditLog:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def log(
        self,
        tool_name: str,
        status: str = "ok",
        app_id: int | None = None,
        duration_ms: float | None = None,
        error: str | None = None,
        **extra: Any,
    ) -> None:
        """Append an audit entry."""
        if not self._enabled:
            return
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "tool": tool_name,
            "status": status,
        }
        if app_id is not None:
            entry["app_id"] = app_id
        if duration_ms is not None:
            entry["duration_ms"] = round(duration_ms, 1)
        if error:
            entry["error"] = error[:500]
        if extra:
            entry["extra"] = extra
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError:
            pass  # Best-effort logging

    def recent(self, limit: int = 50) -> list[dict]:
        """Return recent audit entries (newest first)."""
        if not self._enabled or not self._path.exists():
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            entries = []
            for line in reversed(lines[-limit:]):
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return entries
        except OSError:
            return []


# Module-level singleton
audit = AuditLog.get()
