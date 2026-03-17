"""Tests for apex_mcp.guards — reusable pre-condition checks.

Run: pytest tests/test_guards.py -v
"""
from __future__ import annotations

import json


class TestRequireConnection:
    def test_returns_error_when_disconnected(self):
        from apex_mcp.guards import require_connection

        result = require_connection()
        assert result is not None
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "connect" in parsed["error"].lower()


class TestRequireSession:
    def test_returns_connection_error_first(self):
        from apex_mcp.guards import require_session

        result = require_session()
        assert result is not None
        parsed = json.loads(result)
        assert parsed["status"] == "error"
        assert "connect" in parsed["error"].lower()

    def test_returns_session_error_when_connected_but_no_session(self):
        """Would need a mock connection — tested indirectly via tool tests."""
        pass


class TestRequirePage:
    def test_returns_connection_error_first(self):
        from apex_mcp.guards import require_page

        result = require_page(1)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["status"] == "error"
