"""Tests for apex-mcp tools.

Unit tests (no DB): test input validation, JSON structure, error handling.
Integration tests (marked): require live Oracle ADB connection.

Run all:        pytest tests/ -v
Run unit only:  pytest tests/ -v -m "not integration"
Run integrate:  pytest tests/ -v -m integration
"""
from __future__ import annotations
import json
import pytest


# ── Unit tests: sql_tools ──────────────────────────────────────────────────────

class TestApexRunSqlUnit:
    def test_returns_json_when_not_connected(self):
        from apex_mcp.tools.sql_tools import apex_run_sql
        result = json.loads(apex_run_sql("SELECT 1 FROM DUAL"))
        assert result["status"] == "error"
        assert "connect" in result["error"].lower()

    def test_connect_returns_json(self):
        from apex_mcp.tools.sql_tools import apex_connect
        result_str = apex_connect(
            user="INVALID", password="INVALID", dsn="INVALID",
            wallet_dir="C:/nonexistent", wallet_password="bad"
        )
        result = json.loads(result_str)
        assert result["status"] in ("ok", "error")


class TestApexStatusUnit:
    def test_returns_json_when_disconnected(self):
        from apex_mcp.tools.sql_tools import apex_status
        result = json.loads(apex_status())
        assert "connected" in result
        assert result["connected"] is False
        assert "session" in result


# ── Unit tests: session isolation ─────────────────────────────────────────────

class TestSessionIsolation:
    def test_session_starts_empty(self):
        from apex_mcp.session import session
        assert session.app_id is None
        assert session.import_begun is False
        assert len(session.pages) == 0

    def test_ids_reset_between_tests(self):
        from apex_mcp.ids import ids
        id1 = ids.next("test_a")
        from apex_mcp.ids import IdGenerator
        new_gen = IdGenerator()
        id2 = new_gen.next("test_a")
        # Both generated, both large integers
        assert id1 > 8_000_000_000_000_000
        assert id2 > 8_000_000_000_000_000


# ── Unit tests: component tools (no DB) ───────────────────────────────────────

class TestComponentToolsUnit:
    def test_add_region_errors_without_connection(self):
        from apex_mcp.tools.component_tools import apex_add_region
        result = json.loads(apex_add_region(1, "Test Region"))
        assert result["status"] == "error"

    def test_add_item_errors_without_connection(self):
        from apex_mcp.tools.component_tools import apex_add_item
        result = json.loads(apex_add_item(1, "Test Region", "P1_NAME"))
        assert result["status"] == "error"

    def test_add_dynamic_action_errors_without_connection(self):
        from apex_mcp.tools.component_tools import apex_add_dynamic_action
        result = json.loads(apex_add_dynamic_action(1, "Test DA"))
        assert result["status"] == "error"


# ── Unit tests: validation tools (no DB) ──────────────────────────────────────

class TestValidationToolsUnit:
    def test_validation_errors_without_connection(self):
        from apex_mcp.tools.validation_tools import apex_add_item_validation
        result = json.loads(apex_add_item_validation(1, "P1_NAME", "Name Required"))
        assert result["status"] == "error"

    def test_computation_errors_without_connection(self):
        from apex_mcp.tools.validation_tools import apex_add_item_computation
        result = json.loads(apex_add_item_computation(1, "P1_NAME", computation_expression="'value'"))
        assert result["status"] == "error"


# ── Unit tests: schema tools (no DB) ──────────────────────────────────────────

class TestSchemaToolsUnit:
    def test_list_tables_errors_without_connection(self):
        from apex_mcp.tools.schema_tools import apex_list_tables
        result = json.loads(apex_list_tables())
        assert result["status"] == "error"

    def test_describe_table_errors_without_connection(self):
        from apex_mcp.tools.schema_tools import apex_describe_table
        result = json.loads(apex_describe_table("ANY_TABLE"))
        assert result["status"] == "error"


# ── Unit tests: app tools (no DB) ─────────────────────────────────────────────

class TestAppToolsUnit:
    def test_list_apps_errors_without_connection(self):
        from apex_mcp.tools.app_tools import apex_list_apps
        result = json.loads(apex_list_apps())
        assert result["status"] == "error"
        assert "connect" in result["error"].lower()

    def test_finalize_errors_without_session(self):
        from apex_mcp.tools.app_tools import apex_finalize_app
        result_str = apex_finalize_app()
        # Should complain about missing connection or missing session
        assert "connect" in result_str.lower() or "session" in result_str.lower()


# ── Unit tests: inspect tools (no DB) ─────────────────────────────────────────

class TestInspectToolsUnit:
    def test_get_app_details_errors_without_connection(self):
        from apex_mcp.tools.inspect_tools import apex_get_app_details
        result = json.loads(apex_get_app_details(100))
        assert result["status"] == "error"

    def test_diff_app_errors_without_connection(self):
        from apex_mcp.tools.inspect_tools import apex_diff_app
        result = json.loads(apex_diff_app(100, 200))
        assert result["status"] == "error"


# ── Unit tests: setup tools ────────────────────────────────────────────────────

class TestSetupToolsUnit:
    def test_setup_guide_returns_json(self):
        from apex_mcp.tools.setup_tools import apex_setup_guide
        result = json.loads(apex_setup_guide())
        assert "title" in result
        assert "prerequisites" in result

    def test_check_requirements_returns_json(self):
        from apex_mcp.tools.setup_tools import apex_check_requirements
        result = json.loads(apex_check_requirements())
        assert "checks" in result or "status" in result

    def test_fix_permissions_errors_without_connection(self):
        from apex_mcp.tools.setup_tools import apex_fix_permissions
        result = json.loads(apex_fix_permissions())
        assert result["status"] == "error"


# ── Integration tests: live DB ─────────────────────────────────────────────────

@pytest.mark.integration
class TestConnectionIntegration:
    def test_connect_success(self, connected_db):
        from apex_mcp.tools.sql_tools import apex_status
        result = json.loads(apex_status())
        assert result["connected"] is True
        assert "db_version" in result

    def test_run_sql_select(self, connected_db):
        from apex_mcp.tools.sql_tools import apex_run_sql
        result = json.loads(apex_run_sql("SELECT 1 AS n FROM DUAL"))
        assert result["status"] == "ok"
        assert len(result["rows"]) == 1

    def test_run_sql_with_bind_params(self, connected_db):
        from apex_mcp.tools.sql_tools import apex_run_sql
        result = json.loads(apex_run_sql(
            "SELECT :val AS v FROM DUAL",
            bind_params={"val": "hello"}
        ))
        assert result["status"] == "ok"
        assert result["rows"][0]["V"] == "hello"


@pytest.mark.integration
class TestSchemaIntegration:
    def test_list_tables(self, connected_db):
        from apex_mcp.tools.schema_tools import apex_list_tables
        result = json.loads(apex_list_tables(pattern="TEA_%"))
        assert isinstance(result, list)
        assert len(result) > 0
        assert "table_name" in result[0] or "object_name" in result[0]

    def test_list_views(self, connected_db):
        from apex_mcp.tools.schema_tools import apex_list_tables
        result = json.loads(apex_list_tables(object_type="VIEW"))
        assert isinstance(result, list)

    def test_describe_table_has_sequences_triggers(self, connected_db):
        from apex_mcp.tools.schema_tools import apex_describe_table
        result = json.loads(apex_describe_table("TEA_BENEFICIARIOS"))
        assert "sequences" in result
        assert "triggers" in result
        assert "primary_key" in result
        assert isinstance(result["columns"], list)

    def test_describe_table_not_found(self, connected_db):
        from apex_mcp.tools.schema_tools import apex_describe_table
        result = json.loads(apex_describe_table("NONEXISTENT_TABLE_XYZ"))
        assert result["status"] == "error"


@pytest.mark.integration
class TestAppListIntegration:
    def test_list_apps(self, connected_db):
        from apex_mcp.tools.app_tools import apex_list_apps
        result_str = apex_list_apps()
        result = json.loads(result_str)
        assert isinstance(result, list)
        assert len(result) > 0
        app = result[0]
        assert "APPLICATION_ID" in app
        assert "STATUS" in app


@pytest.mark.integration
class TestInspectIntegration:
    def test_get_app_details(self, connected_db):
        from apex_mcp.tools.inspect_tools import apex_get_app_details
        result = json.loads(apex_get_app_details(100))
        # App 100 is the TEA app
        assert result.get("status") != "error" or "not found" in result.get("error", "")

    def test_diff_app_same(self, connected_db):
        from apex_mcp.tools.inspect_tools import apex_diff_app
        result = json.loads(apex_diff_app(100, 100))
        if result.get("status") == "ok":
            # Diffing an app against itself — pages in both should match all
            diff = result["diff"]
            assert len(diff["pages"]["only_in_app_1"]) == 0
            assert len(diff["pages"]["only_in_app_2"]) == 0
