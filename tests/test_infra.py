"""Infrastructure regression tests for apex-mcp.

Tests that verify correctness of core modules independently of a DB connection.

Run: pytest tests/test_infra.py -v
"""
from __future__ import annotations
import json
import threading


# ── RLock in ConnectionManager ────────────────────────────────────────────────

class TestConnectionManagerLock:
    def test_rlock_in_connection_manager(self):
        """_conn_lock must be an RLock so ensure_connected() can re-enter connect()."""
        from apex_mcp.db import db
        assert isinstance(db._conn_lock, type(threading.RLock())), (
            "_conn_lock must be threading.RLock to prevent deadlock on re-entry"
        )


# ── Session reset captures old app_id ────────────────────────────────────────

class TestSessionReset:
    def test_session_reset_captures_old_app_id(self, caplog):
        """reset() log must include the app_id value that was set before reset."""
        import logging
        from apex_mcp.session import session

        # Prime session with a known app_id
        session.app_id = 999
        session.import_begun = False

        with caplog.at_level(logging.INFO, logger="apex_mcp.session"):
            session.reset()

        assert session.app_id is None
        # The log message must reference the old value, not None
        assert any("999" in record.message for record in caplog.records), (
            "Session reset log must capture app_id=999 before clearing it"
        )


# ── _json() helper ────────────────────────────────────────────────────────────

class TestJsonHelper:
    def test_json_helper_basic(self):
        from apex_mcp.utils import _json
        result = _json({"status": "ok", "count": 3})
        parsed = json.loads(result)
        assert parsed == {"status": "ok", "count": 3}

    def test_json_helper_non_ascii(self):
        from apex_mcp.utils import _json
        result = _json({"msg": "olá mundo"})
        assert "olá mundo" in result, "ensure_ascii=False must preserve non-ASCII chars"

    def test_json_helper_default_str(self):
        """Non-serialisable objects must be stringified, not raise TypeError."""
        from apex_mcp.utils import _json
        import datetime
        result = _json({"ts": datetime.date(2026, 1, 1)})
        parsed = json.loads(result)
        assert "2026" in parsed["ts"]

    def test_json_helper_indent(self):
        from apex_mcp.utils import _json
        result = _json({"a": 1})
        assert "\n" in result, "Output must be indented (multi-line)"


# ── Validators ────────────────────────────────────────────────────────────────

class TestValidators:
    def test_validate_page_id_ok(self):
        from apex_mcp.validators import validate_page_id
        validate_page_id(0)
        validate_page_id(1)
        validate_page_id(9999)

    def test_validate_page_id_negative(self):
        from apex_mcp.validators import validate_page_id
        import pytest
        with pytest.raises(ValueError):
            validate_page_id(-1)

    def test_validate_page_id_non_int(self):
        from apex_mcp.validators import validate_page_id
        import pytest
        with pytest.raises((ValueError, TypeError)):
            validate_page_id("abc")

    def test_validate_app_id_ok(self):
        from apex_mcp.validators import validate_app_id
        validate_app_id(100)
        validate_app_id(9999)

    def test_validate_app_id_zero(self):
        from apex_mcp.validators import validate_app_id
        import pytest
        with pytest.raises(ValueError):
            validate_app_id(0)

    def test_validate_table_name_ok(self):
        from apex_mcp.validators import validate_table_name
        validate_table_name("TEA_BENEFICIARIOS")
        validate_table_name("my_table")

    def test_validate_table_name_empty(self):
        from apex_mcp.validators import validate_table_name
        import pytest
        with pytest.raises(ValueError):
            validate_table_name("")

    def test_validate_table_name_injection(self):
        """SQL injection attempt must be rejected."""
        from apex_mcp.validators import validate_table_name
        import pytest
        with pytest.raises(ValueError):
            validate_table_name("t; DROP TABLE users--")


# ── Config required vars includes WORKSPACE_NAME ─────────────────────────────

class TestConfigRequiredVars:
    def test_workspace_name_in_required_vars(self):
        from apex_mcp.config import _REQUIRED_VARS
        assert "APEX_WORKSPACE_NAME" in _REQUIRED_VARS, (
            "APEX_WORKSPACE_NAME must be in _REQUIRED_VARS to be validated on startup"
        )
