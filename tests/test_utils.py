"""Tests for apex_mcp.utils — shared helpers.

Run: pytest tests/test_utils.py -v
"""
from __future__ import annotations

import json


class TestEsc:
    def test_escapes_single_quotes(self):
        from apex_mcp.utils import _esc

        assert _esc("O'Brien") == "O''Brien"

    def test_no_change_without_quotes(self):
        from apex_mcp.utils import _esc

        assert _esc("hello world") == "hello world"

    def test_empty_string(self):
        from apex_mcp.utils import _esc

        assert _esc("") == ""

    def test_multiple_quotes(self):
        from apex_mcp.utils import _esc

        assert _esc("it's a 'test'") == "it''s a ''test''"


class TestBlk:
    def test_wraps_in_begin_end(self):
        from apex_mcp.utils import _blk

        result = _blk("SELECT 1 FROM DUAL;")
        assert result.startswith("begin\n")
        assert result.endswith("\nend;")

    def test_preserves_content(self):
        from apex_mcp.utils import _blk

        sql = "dbms_output.put_line('hello');"
        result = _blk(sql)
        assert sql in result


class TestJson:
    def test_basic_serialization(self):
        from apex_mcp.utils import _json

        result = _json({"status": "ok", "count": 3})
        parsed = json.loads(result)
        assert parsed == {"status": "ok", "count": 3}

    def test_non_ascii_preserved(self):
        from apex_mcp.utils import _json

        result = _json({"msg": "olá mundo"})
        assert "olá mundo" in result

    def test_non_serializable_uses_str(self):
        import datetime
        from apex_mcp.utils import _json

        result = _json({"ts": datetime.date(2026, 1, 1)})
        parsed = json.loads(result)
        assert "2026" in parsed["ts"]

    def test_output_is_indented(self):
        from apex_mcp.utils import _json

        result = _json({"a": 1})
        assert "\n" in result

    def test_list_serialization(self):
        from apex_mcp.utils import _json

        result = _json([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]

    def test_none_serialization(self):
        from apex_mcp.utils import _json

        result = _json(None)
        assert json.loads(result) is None


class TestSqlToVarchar2:
    def test_single_line(self):
        from apex_mcp.utils import _sql_to_varchar2

        result = _sql_to_varchar2("SELECT 1 FROM DUAL")
        assert "wwv_flow_string.join" in result
        assert "wwv_flow_t_varchar2" in result
        assert "SELECT 1 FROM DUAL" in result

    def test_multi_line(self):
        from apex_mcp.utils import _sql_to_varchar2

        sql = "SELECT *\nFROM my_table\nWHERE 1=1"
        result = _sql_to_varchar2(sql)
        assert result.count("'") >= 6  # at least 3 quoted lines

    def test_empty_returns_empty_string_literal(self):
        from apex_mcp.utils import _sql_to_varchar2

        result = _sql_to_varchar2("")
        assert result == "''"

    def test_escapes_internal_quotes(self):
        from apex_mcp.utils import _sql_to_varchar2

        result = _sql_to_varchar2("SELECT 'hello' FROM DUAL")
        assert "''hello''" in result
