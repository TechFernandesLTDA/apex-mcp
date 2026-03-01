"""Tests for generator_tools: apex_generate_crud, apex_generate_dashboard, apex_generate_login.

Unit tests use unittest.mock to avoid requiring a live Oracle connection.
"""
from __future__ import annotations
import json
import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_session_for_app(app_id: int = 200) -> None:
    """Pre-configure session so tools believe an import session is active."""
    from apex_mcp.session import session
    from apex_mcp.ids import ids
    session.reset()
    ids.reset()
    session.app_id = app_id
    session.import_begun = True
    session.import_ended = False


# ---------------------------------------------------------------------------
# apex_generate_crud
# ---------------------------------------------------------------------------

class TestApexGenerateCrudUnit:
    """Unit tests for apex_generate_crud — no DB required."""

    def test_errors_without_connection(self):
        from apex_mcp.tools.generator_tools import apex_generate_crud
        result = json.loads(apex_generate_crud("MY_TABLE", 10, 11))
        assert result["status"] == "error"
        assert "connect" in result["error"].lower()

    def test_errors_without_session(self):
        from apex_mcp.tools.generator_tools import apex_generate_crud
        from apex_mcp.db import db
        with patch.object(db, "is_connected", return_value=True):
            result = json.loads(apex_generate_crud("MY_TABLE", 10, 11))
        assert result["status"] == "error"
        assert "import session" in result["error"].lower() or "session" in result["error"].lower()

    def test_returns_two_pages_on_success(self):
        """Verify CRUD creates exactly 2 pages (list + form)."""
        from apex_mcp.tools.generator_tools import apex_generate_crud
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)

        # Mock DB responses
        mock_cols = [
            {"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER", "NULLABLE": "N",
             "DATA_LENGTH": 22, "DATA_PRECISION": None},
            {"COLUMN_NAME": "NAME", "DATA_TYPE": "VARCHAR2", "NULLABLE": "Y",
             "DATA_LENGTH": 100, "DATA_PRECISION": None},
        ]
        mock_pk = [{"COLUMN_NAME": "ID"}]

        def mock_execute(sql, params=None):
            sql_upper = sql.upper().strip()
            # PK query: user_constraints + constraint_type = 'P'
            if "CONSTRAINT_TYPE = 'P'" in sql_upper or "CONSTRAINT_TYPE='P'" in sql_upper:
                return mock_pk
            # FK query: user_constraints + constraint_type = 'R'
            if "CONSTRAINT_TYPE = 'R'" in sql_upper or "CONSTRAINT_TYPE='R'" in sql_upper:
                return []  # no FK relationships
            # Column listing query
            if "USER_TAB_COLUMNS" in sql_upper or "ALL_TAB_COLUMNS" in sql_upper:
                return mock_cols
            return []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "execute", side_effect=mock_execute), \
             patch.object(db, "plsql"):
            result = json.loads(apex_generate_crud("MY_TABLE", 10, 11))

        assert result["status"] == "ok", f"Unexpected error: {result.get('error')}"
        assert result.get("list_page_id") == 10
        assert result.get("form_page_id") == 11

    def test_no_invalid_worksheet_params(self):
        """Verify create_worksheet does NOT contain invalid params."""
        from apex_mcp.tools.generator_tools import apex_generate_crud
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)

        captured_plsql: list[str] = []

        mock_cols = [
            {"COLUMN_NAME": "ID", "DATA_TYPE": "NUMBER", "NULLABLE": "N",
             "DATA_LENGTH": 22, "DATA_PRECISION": None},
        ]
        mock_pk = [{"COLUMN_NAME": "ID"}]

        def mock_execute(sql, params=None):
            sql_upper = sql.upper().strip()
            if "CONSTRAINT_TYPE = 'P'" in sql_upper or "CONSTRAINT_TYPE='P'" in sql_upper:
                return mock_pk
            if "CONSTRAINT_TYPE = 'R'" in sql_upper or "CONSTRAINT_TYPE='R'" in sql_upper:
                return []  # no FK relationships
            return mock_cols

        def mock_plsql(body, params=None):
            captured_plsql.append(body)

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "execute", side_effect=mock_execute), \
             patch.object(db, "plsql", side_effect=mock_plsql):
            apex_generate_crud("MY_TABLE", 10, 11)

        worksheet_blocks = [b for b in captured_plsql if "create_worksheet" in b.lower()]
        assert worksheet_blocks, "Expected at least one create_worksheet call"

        for block in worksheet_blocks:
            # These parameters are invalid in APEX 24.2
            assert "p_region_id" not in block, "Invalid p_region_id found in create_worksheet"
            assert "p_max_row_count=>" not in block, "Invalid p_max_row_count found (use p_max_row_count_message)"
            assert "p_show_search_bar" not in block, "Invalid p_show_search_bar found in create_worksheet"
            assert "p_show_actions_menu" not in block, "Invalid p_show_actions_menu found in create_worksheet"
            assert "p_owner" not in block, "Invalid p_owner found in create_worksheet"


# ---------------------------------------------------------------------------
# apex_generate_login
# ---------------------------------------------------------------------------

class TestApexGenerateLoginUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.generator_tools import apex_generate_login
        result = json.loads(apex_generate_login())
        assert result["status"] == "error"

    def test_creates_login_page(self):
        from apex_mcp.tools.generator_tools import apex_generate_login
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)

        captured_plsql: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured_plsql.append(b)):
            result = json.loads(apex_generate_login(page_id=101))

        assert result["status"] == "ok", f"Unexpected error: {result.get('error')}"
        # Verify a page was created
        assert any("create_page" in b for b in captured_plsql), "Expected create_page call"
        # Verify login page is in session
        assert 101 in session.pages


# ---------------------------------------------------------------------------
# apex_generate_dashboard
# ---------------------------------------------------------------------------

class TestApexGenerateDashboardUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.generator_tools import apex_generate_dashboard
        result = json.loads(apex_generate_dashboard(page_id=1))
        assert result["status"] == "error"

    def test_creates_kpi_regions(self):
        from apex_mcp.tools.generator_tools import apex_generate_dashboard
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)
        session.pages[1] = __import__("apex_mcp.session", fromlist=["PageInfo"]).PageInfo(
            page_id=1, page_name="Dashboard", page_type="dashboard"
        )

        kpis = [
            {"label": "Total", "sql": "SELECT COUNT(*) FROM DUAL"},
            {"label": "Active", "sql": "SELECT 1 FROM DUAL"},
        ]

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_generate_dashboard(page_id=1, kpi_queries=kpis))

        assert result["status"] == "ok", f"Unexpected error: {result.get('error')}"
        assert result.get("kpi_count") == 2
