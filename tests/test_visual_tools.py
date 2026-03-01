"""Tests for visual_tools: apex_add_jet_chart, apex_add_gauge, apex_add_calendar, apex_add_sparkline.

Unit tests use unittest.mock to avoid requiring a live Oracle connection.
"""
from __future__ import annotations
import json
import pytest
from unittest.mock import patch, MagicMock


def _setup_session_for_page(page_id: int, app_id: int = 200) -> None:
    from apex_mcp.session import session, PageInfo
    from apex_mcp.ids import ids
    session.reset()
    ids.reset()
    session.app_id = app_id
    session.import_begun = True
    session.import_ended = False
    session.pages[page_id] = PageInfo(page_id=page_id, page_name="Test", page_type="blank")


# ---------------------------------------------------------------------------
# apex_add_jet_chart
# ---------------------------------------------------------------------------

class TestApexAddJetChartUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.visual_tools import apex_add_jet_chart
        result = json.loads(apex_add_jet_chart(1, "Chart", sql_query="SELECT 1 L, 1 V FROM DUAL"))
        assert result["status"] == "error"

    def test_no_p_init_javascript_code_in_plsql(self):
        """Verify p_init_javascript_code is never passed to create_jet_chart."""
        from apex_mcp.tools.visual_tools import apex_add_jet_chart
        from apex_mcp.db import db

        _setup_session_for_page(1)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            apex_add_jet_chart(
                page_id=1,
                region_name="Test Chart",
                chart_type="bar",
                sql_query="SELECT 'A' LABEL, 1 VALUE FROM DUAL",
                color_palette=["#00995D", "#1E88E5"],  # should be ignored
            )

        jet_chart_blocks = [b for b in captured if "create_jet_chart(" in b]
        assert jet_chart_blocks, "Expected create_jet_chart call"
        for block in jet_chart_blocks:
            assert "p_init_javascript_code" not in block, \
                "p_init_javascript_code should NOT be passed to create_jet_chart in APEX 24.2"

    def test_creates_region_in_session(self):
        from apex_mcp.tools.visual_tools import apex_add_jet_chart
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_page(5)

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_add_jet_chart(
                page_id=5,
                region_name="Revenue Chart",
                chart_type="line",
                sql_query="SELECT 'Jan' LABEL, 100 VALUE FROM DUAL",
            ))

        assert result["status"] == "ok"
        assert result["chart_type"] == "line"
        assert len(session.regions) >= 1


# ---------------------------------------------------------------------------
# apex_add_gauge
# ---------------------------------------------------------------------------

class TestApexAddGaugeUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.visual_tools import apex_add_gauge
        result = json.loads(apex_add_gauge(1, "Gauge", "SELECT 75 VALUE FROM DUAL"))
        assert result["status"] == "error"

    def test_creates_dial_chart(self):
        """Verify gauge creates a chart with type 'dial'."""
        from apex_mcp.tools.visual_tools import apex_add_gauge
        from apex_mcp.db import db

        _setup_session_for_page(1)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_add_gauge(
                page_id=1,
                region_name="Score Gauge",
                sql_query="SELECT 75 VALUE FROM DUAL",
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"
        assert result.get("chart_type") == "dial"

        jet_chart_blocks = [b for b in captured if "create_jet_chart(" in b]
        assert jet_chart_blocks
        for block in jet_chart_blocks:
            assert "p_init_javascript_code" not in block, \
                "p_init_javascript_code should not be used"
            assert "'dial'" in block, "Gauge should use chart_type='dial'"


# ---------------------------------------------------------------------------
# apex_add_calendar
# ---------------------------------------------------------------------------

class TestApexAddCalendarUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.visual_tools import apex_add_calendar
        result = json.loads(apex_add_calendar(
            1, "Calendar", "SELECT SYSDATE D, 'Event' T FROM DUAL",
            date_column="D", title_column="T"
        ))
        assert result["status"] == "error"

    def test_uses_native_css_calendar(self):
        """Verify calendar uses NATIVE_CSS_CALENDAR, NOT NATIVE_JET_CHART."""
        from apex_mcp.tools.visual_tools import apex_add_calendar
        from apex_mcp.db import db

        _setup_session_for_page(1)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_add_calendar(
                page_id=1,
                region_name="Event Calendar",
                sql_query="SELECT DT_AVALIACAO, DS_NOME FROM TEA_AVALIACOES",
                date_column="DT_AVALIACAO",
                title_column="DS_NOME",
                display_as="month",
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"

        all_plsql = "\n".join(captured)
        assert "NATIVE_CSS_CALENDAR" in all_plsql, \
            "Calendar should use NATIVE_CSS_CALENDAR"
        assert "NATIVE_JET_CHART" not in all_plsql, \
            "Calendar should NOT use NATIVE_JET_CHART"
        assert "create_jet_chart(" not in all_plsql, \
            "Calendar should NOT call create_jet_chart"
        assert "create_jet_chart_series" not in all_plsql, \
            "Calendar should NOT call create_jet_chart_series"

    def test_calendar_passes_columns_as_attributes(self):
        """Verify date_column and title_column appear as p_attribute_01/02."""
        from apex_mcp.tools.visual_tools import apex_add_calendar
        from apex_mcp.db import db

        _setup_session_for_page(2)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            apex_add_calendar(
                page_id=2,
                region_name="Calendar",
                sql_query="SELECT DT, TITULO FROM EVENTOS",
                date_column="DT",
                title_column="TITULO",
                end_date_column="DT_FIM",
            )

        all_plsql = "\n".join(captured)
        assert "p_attribute_01=>'DT'" in all_plsql
        assert "p_attribute_02=>'TITULO'" in all_plsql
        assert "p_attribute_04=>'DT_FIM'" in all_plsql

    def test_invalid_display_as_returns_error(self):
        from apex_mcp.tools.visual_tools import apex_add_calendar
        from apex_mcp.db import db

        _setup_session_for_page(1)

        with patch.object(db, "is_connected", return_value=True):
            result = json.loads(apex_add_calendar(
                1, "Cal", "SELECT SYSDATE D, 'E' T FROM DUAL",
                date_column="D", title_column="T", display_as="invalid_view"
            ))

        assert result["status"] == "error"
        assert "display_as" in result["error"].lower() or "invalid" in result["error"].lower()


# ---------------------------------------------------------------------------
# apex_add_sparkline
# ---------------------------------------------------------------------------

class TestApexAddSparklineUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.visual_tools import apex_add_sparkline
        result = json.loads(apex_add_sparkline(1, "Metrics", [{"label": "X", "sql": "SELECT 1 FROM DUAL"}]))
        assert result["status"] == "error"

    def test_creates_region_on_success(self):
        from apex_mcp.tools.visual_tools import apex_add_sparkline
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_page(1)

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_add_sparkline(
                page_id=1,
                region_name="KPI Cards",
                metrics=[
                    {"label": "Total", "sql": "SELECT COUNT(*) V FROM DUAL"},
                    {"label": "Active", "sql": "SELECT 5 V FROM DUAL"},
                ],
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"
        assert len(session.regions) >= 1
