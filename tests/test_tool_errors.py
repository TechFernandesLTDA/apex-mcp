"""Tests for tool error paths (no DB connection required).

Ensures all tools return proper JSON error responses when called without
a live database connection or active session.

Run: pytest tests/test_tool_errors.py -v
"""
from __future__ import annotations

import json

import pytest


# ── Page tools ───────────────────────────────────────────────────────────────

class TestPageToolsErrors:
    def test_add_page_not_connected(self):
        from apex_mcp.tools.page_tools import apex_add_page

        result = json.loads(apex_add_page(1, "Test"))
        assert result["status"] == "error"
        assert "connect" in result["error"].lower()

    def test_add_page_invalid_id(self):
        from apex_mcp.tools.page_tools import apex_add_page

        result = json.loads(apex_add_page(-1, "Test"))
        assert result["status"] == "error"
        assert "page_id" in result["error"].lower()

    def test_list_pages_not_connected(self):
        from apex_mcp.tools.page_tools import apex_list_pages

        result = json.loads(apex_list_pages())
        assert result["status"] == "error"


# ── Shared tools ──────────────────────────────────────────────────────────────

class TestSharedToolsErrors:
    def test_add_lov_not_connected(self):
        from apex_mcp.tools.shared_tools import apex_add_lov

        result = json.loads(apex_add_lov("TEST_LOV"))
        assert result["status"] == "error"

    def test_add_auth_scheme_not_connected(self):
        from apex_mcp.tools.shared_tools import apex_add_auth_scheme

        result = json.loads(apex_add_auth_scheme("IS_ADMIN", "return true;"))
        assert result["status"] == "error"

    def test_add_nav_item_not_connected(self):
        from apex_mcp.tools.shared_tools import apex_add_nav_item

        result = json.loads(apex_add_nav_item("Home", 1))
        assert result["status"] == "error"

    def test_add_app_item_not_connected(self):
        from apex_mcp.tools.shared_tools import apex_add_app_item

        result = json.loads(apex_add_app_item("APP_ROLE"))
        assert result["status"] == "error"

    def test_add_app_process_not_connected(self):
        from apex_mcp.tools.shared_tools import apex_add_app_process

        result = json.loads(apex_add_app_process("INIT", "begin null; end;"))
        assert result["status"] == "error"


# ── JS tools ──────────────────────────────────────────────────────────────────

class TestJsToolsErrors:
    def test_add_page_js_not_connected(self):
        from apex_mcp.tools.js_tools import apex_add_page_js

        result = json.loads(apex_add_page_js(1, "alert(1);"))
        assert result["status"] == "error"

    def test_add_global_js_empty_name(self):
        from apex_mcp.tools.js_tools import apex_add_global_js

        result = json.loads(apex_add_global_js("", "code"))
        assert result["status"] == "error"

    def test_add_global_js_empty_code(self):
        from apex_mcp.tools.js_tools import apex_add_global_js

        result = json.loads(apex_add_global_js("MY_LIB", ""))
        assert result["status"] == "error"

    def test_add_global_js_returns_ok_without_db(self):
        """apex_add_global_js doesn't need DB — returns JS content."""
        from apex_mcp.tools.js_tools import apex_add_global_js

        result = json.loads(apex_add_global_js("MY_LIB", "function x() {}"))
        assert result["status"] == "ok"
        assert "js_content" in result
        assert "my-lib.js" in result["filename"]

    def test_generate_ajax_handler_not_connected(self):
        from apex_mcp.tools.js_tools import apex_generate_ajax_handler

        result = json.loads(apex_generate_ajax_handler(1, "SEARCH", "begin null; end;"))
        assert result["status"] == "error"


# ── DevOps tools ─────────────────────────────────────────────────────────────

class TestDevopsToolsErrors:
    def test_generate_rest_not_connected(self):
        from apex_mcp.tools.devops_tools import apex_generate_rest_endpoints

        result = json.loads(apex_generate_rest_endpoints("MY_TABLE"))
        assert result["status"] == "error"

    def test_generate_rest_invalid_table(self):
        from apex_mcp.tools.devops_tools import apex_generate_rest_endpoints

        result = json.loads(apex_generate_rest_endpoints("1INVALID"))
        assert result["status"] == "error"

    def test_export_page_not_connected(self):
        from apex_mcp.tools.devops_tools import apex_export_page

        result = json.loads(apex_export_page(100, 1))
        assert result["status"] == "error"

    def test_generate_docs_not_connected(self):
        from apex_mcp.tools.devops_tools import apex_generate_docs

        result = json.loads(apex_generate_docs())
        assert result["status"] == "error"

    def test_begin_batch_always_ok(self):
        from apex_mcp.tools.devops_tools import apex_begin_batch

        result = json.loads(apex_begin_batch())
        assert result["status"] == "ok"
        # Clean up
        from apex_mcp.db import db
        db.rollback_batch()

    def test_commit_batch_empty_queue(self):
        from apex_mcp.tools.devops_tools import apex_commit_batch

        result = json.loads(apex_commit_batch())
        assert result["status"] == "ok"
        assert result["executed"] == 0


# ── User tools ────────────────────────────────────────────────────────────────

class TestUserToolsErrors:
    def test_create_user_not_connected(self):
        from apex_mcp.tools.user_tools import apex_create_user

        result = json.loads(apex_create_user("test", "password123"))
        assert result["status"] == "error"

    def test_create_user_empty_username(self):
        from apex_mcp.tools.user_tools import apex_create_user

        result = json.loads(apex_create_user("", "password123"))
        assert result["status"] == "error"

    def test_create_user_short_password(self):
        """Short password is caught, but connection check comes first when disconnected."""
        from apex_mcp.tools.user_tools import apex_create_user

        result = json.loads(apex_create_user("user1", "12345"))
        assert result["status"] == "error"
        # When disconnected, connection error takes precedence;
        # password length is validated after connection check

    def test_list_users_not_connected(self):
        from apex_mcp.tools.user_tools import apex_list_users

        result = json.loads(apex_list_users())
        assert result["status"] == "error"


# ── Visual/Chart tools ────────────────────────────────────────────────────────

class TestChartToolsErrors:
    def test_stacked_chart_not_connected(self):
        from apex_mcp.tools.chart_tools import apex_add_stacked_chart

        result = json.loads(apex_add_stacked_chart(
            1, "Test",
            [{"name": "S1", "sql": "SELECT 1"}, {"name": "S2", "sql": "SELECT 2"}],
        ))
        assert result["status"] == "error"

    def test_stacked_chart_too_few_series(self):
        """Guard should catch missing page even before series check."""
        from apex_mcp.tools.chart_tools import apex_add_stacked_chart

        result = json.loads(apex_add_stacked_chart(1, "Test", [{"name": "S1"}]))
        assert result["status"] == "error"

    def test_combo_chart_not_connected(self):
        from apex_mcp.tools.chart_tools import apex_add_combo_chart

        result = json.loads(apex_add_combo_chart(1, "Test", "SELECT 1", "SELECT 2"))
        assert result["status"] == "error"

    def test_bubble_chart_not_connected(self):
        from apex_mcp.tools.chart_tools import apex_add_bubble_chart

        result = json.loads(apex_add_bubble_chart(1, "Test", "SELECT 1"))
        assert result["status"] == "error"

    def test_scatter_plot_not_connected(self):
        from apex_mcp.tools.chart_tools import apex_add_scatter_plot

        result = json.loads(apex_add_scatter_plot(1, "Test", "SELECT 1"))
        assert result["status"] == "error"

    def test_range_chart_not_connected(self):
        from apex_mcp.tools.chart_tools import apex_add_range_chart

        result = json.loads(apex_add_range_chart(1, "Test", "SELECT 1"))
        assert result["status"] == "error"


# ── Validation tools ──────────────────────────────────────────────────────────

class TestValidationToolsErrors:
    def test_add_validation_not_connected(self):
        from apex_mcp.tools.validation_tools import apex_add_item_validation

        result = json.loads(apex_add_item_validation(1, "P1_NAME", "Required"))
        assert result["status"] == "error"

    def test_add_computation_not_connected(self):
        from apex_mcp.tools.validation_tools import apex_add_item_computation

        result = json.loads(apex_add_item_computation(1, "P1_X"))
        assert result["status"] == "error"


# ── Component tools ───────────────────────────────────────────────────────────

class TestComponentToolsErrors:
    def test_add_button_not_connected(self):
        from apex_mcp.tools.component_tools import apex_add_button

        result = json.loads(apex_add_button(1, "Region", "SAVE", "Save"))
        assert result["status"] == "error"

    def test_add_process_not_connected(self):
        from apex_mcp.tools.component_tools import apex_add_process

        result = json.loads(apex_add_process(1, "Save DML"))
        assert result["status"] == "error"


# ── App tools ─────────────────────────────────────────────────────────────────

class TestAppToolsErrors:
    def test_create_app_invalid_id(self):
        from apex_mcp.tools.app_tools import apex_create_app

        result = json.loads(apex_create_app(app_id=50, app_name="Test"))
        assert result["status"] == "error"
        assert "app_id" in result["error"].lower()

    def test_delete_app_not_connected(self):
        from apex_mcp.tools.app_tools import apex_delete_app

        result = json.loads(apex_delete_app(200))
        assert result["status"] == "error"

    def test_export_app_not_connected(self):
        from apex_mcp.tools.app_tools import apex_export_app

        result = json.loads(apex_export_app(200))
        assert result["status"] == "error"

    def test_describe_page_not_connected(self):
        from apex_mcp.tools.app_tools import apex_describe_page

        result = json.loads(apex_describe_page(200, 1))
        assert result["status"] == "error"

    def test_dry_run_enable_returns_ok(self):
        from apex_mcp.tools.app_tools import apex_dry_run_preview
        from apex_mcp.db import db

        result = json.loads(apex_dry_run_preview(True))
        assert result["status"] == "ok"
        assert result["mode"] == "dry_run_enabled"
        # Clean up
        db.disable_dry_run()

    def test_dry_run_disable_returns_log(self):
        from apex_mcp.tools.app_tools import apex_dry_run_preview
        from apex_mcp.db import db

        db.enable_dry_run()
        result = json.loads(apex_dry_run_preview(False))
        assert result["status"] == "ok"
        assert "plsql_log" in result


# ── Setup tools ───────────────────────────────────────────────────────────────

class TestSetupToolsErrors:
    def test_check_permissions_not_connected(self):
        from apex_mcp.tools.setup_tools import apex_check_permissions

        result = json.loads(apex_check_permissions())
        assert "error" in result

    def test_setup_guide_structure(self):
        from apex_mcp.tools.setup_tools import apex_setup_guide

        result = json.loads(apex_setup_guide())
        assert "prerequisites" in result
        assert "environment_variables" in result
        assert "quick_start" in result
        assert "troubleshooting" in result

    def test_check_requirements_structure(self):
        from apex_mcp.tools.setup_tools import apex_check_requirements

        result = json.loads(apex_check_requirements())
        assert "checks" in result
        assert "summary" in result


# ── Schema tools ──────────────────────────────────────────────────────────────

class TestSchemaToolsErrors:
    def test_detect_relationships_not_connected(self):
        from apex_mcp.tools.schema_tools import apex_detect_relationships

        result = json.loads(apex_detect_relationships(["TABLE_A"]))
        assert result["status"] == "error"

    def test_detect_relationships_empty_list(self):
        from apex_mcp.tools.schema_tools import apex_detect_relationships

        result = json.loads(apex_detect_relationships([]))
        assert result["status"] == "error"

    def test_list_tables_invalid_type(self):
        from apex_mcp.tools.schema_tools import apex_list_tables

        result = json.loads(apex_list_tables(object_type="INVALID"))
        assert result["status"] == "error"
