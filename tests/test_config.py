"""Tests for apex_mcp.config — configuration constants.

Run: pytest tests/test_config.py -v
"""
from __future__ import annotations


class TestConfigConstants:
    def test_apex_version_format(self):
        from apex_mcp.config import APEX_VERSION

        parts = APEX_VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_compat_mode_format(self):
        from apex_mcp.config import APEX_COMPAT_MODE

        assert "." in APEX_COMPAT_MODE

    def test_default_date_format(self):
        from apex_mcp.config import DEFAULT_DATE_FORMAT

        assert DEFAULT_DATE_FORMAT == "DD/MM/YYYY"

    def test_default_language(self):
        from apex_mcp.config import DEFAULT_LANGUAGE

        assert DEFAULT_LANGUAGE == "pt-br"


class TestRequiredVars:
    def test_workspace_name_in_required_vars(self):
        from apex_mcp.config import _REQUIRED_VARS

        assert "APEX_WORKSPACE_NAME" in _REQUIRED_VARS

    def test_all_oracle_vars_present(self):
        from apex_mcp.config import _REQUIRED_VARS

        for var in ["ORACLE_DB_USER", "ORACLE_DB_PASS", "ORACLE_DSN",
                     "ORACLE_WALLET_DIR"]:
            assert var in _REQUIRED_VARS

    def test_workspace_id_is_int(self):
        from apex_mcp.config import WORKSPACE_ID

        assert isinstance(WORKSPACE_ID, int)


class TestTypeAnnotations:
    def test_string_types(self):
        from apex_mcp.config import DB_USER, DB_PASS, DB_DSN, WALLET_DIR, WALLET_PASS

        for val in (DB_USER, DB_PASS, DB_DSN, WALLET_DIR, WALLET_PASS):
            assert isinstance(val, str)

    def test_apex_schema_is_str(self):
        from apex_mcp.config import APEX_SCHEMA

        assert isinstance(APEX_SCHEMA, str)
