"""Tests for advanced_tools: apex_generate_wizard, apex_generate_report_page,
apex_add_notification_region, apex_add_breadcrumb, apex_add_timeline.

Unit tests use unittest.mock to avoid requiring a live Oracle connection.
"""
from __future__ import annotations
import json
import pytest
from unittest.mock import patch, MagicMock


def _setup_session_for_app(app_id: int = 200) -> None:
    from apex_mcp.session import session
    from apex_mcp.ids import ids
    session.reset()
    ids.reset()
    session.app_id = app_id
    session.import_begun = True
    session.import_ended = False


def _setup_session_with_page(page_id: int, app_id: int = 200) -> None:
    from apex_mcp.session import session, PageInfo
    from apex_mcp.ids import ids
    session.reset()
    ids.reset()
    session.app_id = app_id
    session.import_begun = True
    session.import_ended = False
    session.pages[page_id] = PageInfo(page_id=page_id, page_name="Test", page_type="blank")


# ---------------------------------------------------------------------------
# apex_generate_wizard
# ---------------------------------------------------------------------------

class TestApexGenerateWizardUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.advanced_tools import apex_generate_wizard
        result = json.loads(apex_generate_wizard(
            start_page_id=50,
            steps=[{"title": "Step 1", "items": []}],
        ))
        assert result["status"] == "error"

    def test_no_request_is_contained_in_value_in_branches(self):
        """Verify wizard branches use PLSQL_EXPRESSION, not REQUEST_IS_CONTAINED_IN_VALUE."""
        from apex_mcp.tools.advanced_tools import apex_generate_wizard
        from apex_mcp.db import db

        _setup_session_for_app(200)

        captured: list[str] = []

        steps = [
            {"title": "Step 1: Basic Info", "items": [
                {"name": "NOME", "label": "Name", "type": "text"}
            ]},
            {"title": "Step 2: Details", "items": [
                {"name": "EMAIL", "label": "Email", "type": "text"}
            ]},
        ]

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_generate_wizard(start_page_id=50, steps=steps))

        assert result["status"] == "ok", f"Error: {result.get('error')}"

        all_plsql = "\n".join(captured)
        assert "REQUEST_IS_CONTAINED_IN_VALUE" not in all_plsql, \
            "Wizard branches must NOT use REQUEST_IS_CONTAINED_IN_VALUE (invalid for branches)"

        # Verify PLSQL_EXPRESSION is used for branches instead
        branch_blocks = [b for b in captured if "create_page_branch" in b]
        assert branch_blocks, "Expected at least one create_page_branch"
        for block in branch_blocks:
            if "p_branch_condition_type" in block:
                assert "PLSQL_EXPRESSION" in block, \
                    "Branch condition type must be PLSQL_EXPRESSION"

    def test_next_button_uses_submit_not_redirect(self):
        """Verify Next button uses p_button_action=>'SUBMIT', not REDIRECT_URL."""
        from apex_mcp.tools.advanced_tools import apex_generate_wizard
        from apex_mcp.db import db

        _setup_session_for_app(200)

        captured: list[str] = []
        steps = [
            {"title": "Step 1", "items": [{"name": "FIELD1", "label": "Field 1", "type": "text"}]},
            {"title": "Step 2", "items": [{"name": "FIELD2", "label": "Field 2", "type": "text"}]},
        ]

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            apex_generate_wizard(start_page_id=50, steps=steps)

        all_plsql = "\n".join(captured)
        # Check that buttons with NEXT name use SUBMIT action
        button_blocks = [b for b in captured if "create_page_button" in b and "NEXT" in b]
        for block in button_blocks:
            assert "SUBMIT" in block, "Next button must use p_button_action=>'SUBMIT'"
            assert "REDIRECT_URL" not in block, "Next button must NOT use REDIRECT_URL"

    def test_creates_correct_number_of_pages(self):
        from apex_mcp.tools.advanced_tools import apex_generate_wizard
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)

        steps = [
            {"title": "Step 1", "items": []},
            {"title": "Step 2", "items": []},
            {"title": "Step 3", "items": []},
        ]

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_generate_wizard(start_page_id=50, steps=steps))

        assert result["status"] == "ok", f"Error: {result.get('error')}"
        assert len(session.pages) == 3


# ---------------------------------------------------------------------------
# apex_generate_report_page
# ---------------------------------------------------------------------------

class TestApexGenerateReportPageUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.advanced_tools import apex_generate_report_page
        result = json.loads(apex_generate_report_page(
            5, "My Report", "SELECT * FROM DUAL"
        ))
        assert result["status"] == "error"

    def test_no_invalid_worksheet_params(self):
        """Verify create_worksheet does NOT contain invalid params."""
        from apex_mcp.tools.advanced_tools import apex_generate_report_page
        from apex_mcp.db import db

        _setup_session_for_app(200)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_generate_report_page(
                page_id=5,
                page_name="My Report",
                sql_query="SELECT * FROM DUAL",
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"

        worksheet_blocks = [b for b in captured if "create_worksheet" in b.lower()]
        for block in worksheet_blocks:
            assert "p_region_id" not in block, "p_region_id is invalid in create_worksheet"
            assert "p_max_row_count=>" not in block, "p_max_row_count is invalid (use p_max_row_count_message)"
            assert "p_show_search_bar" not in block, "p_show_search_bar is invalid in create_worksheet"
            assert "p_show_actions_menu" not in block, "p_show_actions_menu is invalid in create_worksheet"
            assert "p_owner" not in block, "p_owner is invalid in create_worksheet"

    def test_creates_ir_region(self):
        from apex_mcp.tools.advanced_tools import apex_generate_report_page
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_for_app(200)

        captured: list[str] = []

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_generate_report_page(
                5, "Report", "SELECT * FROM DUAL"
            ))

        assert result["status"] == "ok"
        ir_blocks = [b for b in captured if "NATIVE_IR" in b]
        assert ir_blocks, "Expected NATIVE_IR region creation"


# ---------------------------------------------------------------------------
# apex_add_notification_region
# ---------------------------------------------------------------------------

class TestApexAddNotificationRegionUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.advanced_tools import apex_add_notification_region
        result = json.loads(apex_add_notification_region(1, "Info", "Hello world"))
        assert result["status"] == "error"

    def test_creates_static_region(self):
        from apex_mcp.tools.advanced_tools import apex_add_notification_region
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_with_page(1)

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_add_notification_region(
                page_id=1,
                region_name="Info Alert",
                message="This is a test notification.",
                notification_type="info",
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"
        assert len(session.regions) >= 1


# ---------------------------------------------------------------------------
# apex_add_breadcrumb
# ---------------------------------------------------------------------------

class TestApexAddBreadcrumbUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.advanced_tools import apex_add_breadcrumb
        result = json.loads(apex_add_breadcrumb(1, "Breadcrumb", [{"label": "Home", "page_id": 1}]))
        assert result["status"] == "error"

    def test_creates_breadcrumb_region(self):
        from apex_mcp.tools.advanced_tools import apex_add_breadcrumb
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_with_page(5)

        captured: list[str] = []
        entries = [
            {"label": "Home", "page_id": 1},
            {"label": "Reports", "page_id": 5},
        ]

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql", side_effect=lambda b, p=None: captured.append(b)):
            result = json.loads(apex_add_breadcrumb(page_id=5, region_name="Nav Breadcrumb", entries=entries))

        assert result["status"] == "ok", f"Error: {result.get('error')}"


# ---------------------------------------------------------------------------
# apex_add_timeline
# ---------------------------------------------------------------------------

class TestApexAddTimelineUnit:
    def test_errors_without_connection(self):
        from apex_mcp.tools.advanced_tools import apex_add_timeline
        result = json.loads(apex_add_timeline(
            1, "History", "SELECT SYSDATE DT, 'Event' TITLE, 'Desc' BODY FROM DUAL",
            date_col="DT", title_col="TITLE", body_col="BODY"
        ))
        assert result["status"] == "error"

    def test_creates_timeline_region(self):
        from apex_mcp.tools.advanced_tools import apex_add_timeline
        from apex_mcp.db import db
        from apex_mcp.session import session

        _setup_session_with_page(10)

        with patch.object(db, "is_connected", return_value=True), \
             patch.object(db, "plsql"):
            result = json.loads(apex_add_timeline(
                page_id=10,
                region_name="Activity Timeline",
                sql_query="SELECT SYSDATE DT, 'Event' TITLE, 'Desc' BODY FROM DUAL",
                date_col="DT",
                title_col="TITLE",
                body_col="BODY",
            ))

        assert result["status"] == "ok", f"Error: {result.get('error')}"
        assert len(session.regions) >= 1
