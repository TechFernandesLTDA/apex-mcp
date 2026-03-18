"""Tests for audit trail module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


def test_audit_log_creates_file():
    """Test that audit log creates the audit file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from apex_mcp.audit import AuditLog
        log = AuditLog(path=Path(tmpdir) / "test_audit.jsonl")
        log.log("apex_connect", status="ok")
        assert (Path(tmpdir) / "test_audit.jsonl").exists()


def test_audit_log_writes_json():
    """Test that audit entries are valid JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from apex_mcp.audit import AuditLog
        log = AuditLog(path=Path(tmpdir) / "test_audit.jsonl")
        log.log("apex_create_app", status="ok", app_id=200, duration_ms=150.3)

        with open(Path(tmpdir) / "test_audit.jsonl") as f:
            line = f.readline()
        entry = json.loads(line)
        assert entry["tool"] == "apex_create_app"
        assert entry["status"] == "ok"
        assert entry["app_id"] == 200
        assert entry["duration_ms"] == 150.3


def test_audit_log_recent():
    """Test that recent() returns entries newest first."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from apex_mcp.audit import AuditLog
        log = AuditLog(path=Path(tmpdir) / "test_audit.jsonl")
        log.log("first", status="ok")
        log.log("second", status="ok")
        log.log("third", status="ok")

        entries = log.recent(limit=2)
        assert len(entries) == 2
        assert entries[0]["tool"] == "third"
        assert entries[1]["tool"] == "second"


def test_audit_log_error_entry():
    """Test that error entries are properly logged."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from apex_mcp.audit import AuditLog
        log = AuditLog(path=Path(tmpdir) / "test_audit.jsonl")
        log.log("apex_run_sql", status="error", error="ORA-00942: table does not exist")

        entries = log.recent()
        assert entries[0]["error"] == "ORA-00942: table does not exist"


def test_audit_log_truncates_long_errors():
    """Test that long error messages are truncated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from apex_mcp.audit import AuditLog
        log = AuditLog(path=Path(tmpdir) / "test_audit.jsonl")
        long_error = "x" * 1000
        log.log("test", status="error", error=long_error)

        entries = log.recent()
        assert len(entries[0]["error"]) == 500
