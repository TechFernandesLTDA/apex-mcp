"""Extended tests for apex_mcp.validators — full coverage.

Run: pytest tests/test_validators_extended.py -v
"""
from __future__ import annotations

import pytest


class TestValidateChartType:
    def test_valid_types(self):
        from apex_mcp.validators import validate_chart_type

        for ct in ("bar", "line", "pie", "donut", "area", "scatter", "bubble",
                    "funnel", "dial", "radar", "range", "combo"):
            assert validate_chart_type(ct) == ct

    def test_case_insensitive(self):
        from apex_mcp.validators import validate_chart_type

        assert validate_chart_type("BAR") == "bar"
        assert validate_chart_type("Line") == "line"

    def test_strips_whitespace(self):
        from apex_mcp.validators import validate_chart_type

        assert validate_chart_type("  pie  ") == "pie"

    def test_invalid_raises(self):
        from apex_mcp.validators import validate_chart_type

        with pytest.raises(ValueError, match="not valid"):
            validate_chart_type("histogram")


class TestValidateItemType:
    def test_valid_types(self):
        from apex_mcp.validators import validate_item_type

        for it in ("TEXT_FIELD", "TEXTAREA", "NUMBER_FIELD", "DATE_PICKER",
                    "SELECT_LIST", "CHECKBOX", "RADIO_GROUP", "SWITCH", "HIDDEN",
                    "DISPLAY_ONLY", "FILE_BROWSE", "PASSWORD", "RICH_TEXT"):
            assert validate_item_type(it) == it

    def test_case_insensitive(self):
        from apex_mcp.validators import validate_item_type

        assert validate_item_type("text_field") == "TEXT_FIELD"

    def test_invalid_raises(self):
        from apex_mcp.validators import validate_item_type

        with pytest.raises(ValueError, match="not valid"):
            validate_item_type("SLIDER")


class TestValidateSequence:
    def test_valid_sequences(self):
        from apex_mcp.validators import validate_sequence

        assert validate_sequence(1) == 1
        assert validate_sequence(10) == 10
        assert validate_sequence(99999) == 99999

    def test_zero_raises(self):
        from apex_mcp.validators import validate_sequence

        with pytest.raises(ValueError):
            validate_sequence(0)

    def test_negative_raises(self):
        from apex_mcp.validators import validate_sequence

        with pytest.raises(ValueError):
            validate_sequence(-5)

    def test_too_large_raises(self):
        from apex_mcp.validators import validate_sequence

        with pytest.raises(ValueError):
            validate_sequence(100000)

    def test_non_int_raises(self):
        from apex_mcp.validators import validate_sequence

        with pytest.raises(ValueError):
            validate_sequence("10")  # type: ignore[arg-type]


class TestValidateColorHex:
    def test_valid_6_digit(self):
        from apex_mcp.validators import validate_color_hex

        assert validate_color_hex("#FF0000") == "#FF0000"
        assert validate_color_hex("#00ff00") == "#00FF00"

    def test_valid_3_digit(self):
        from apex_mcp.validators import validate_color_hex

        assert validate_color_hex("#F00") == "#F00"
        assert validate_color_hex("#abc") == "#ABC"

    def test_strips_whitespace(self):
        from apex_mcp.validators import validate_color_hex

        assert validate_color_hex("  #FF0000  ") == "#FF0000"

    def test_invalid_no_hash(self):
        from apex_mcp.validators import validate_color_hex

        with pytest.raises(ValueError, match="Invalid hex color"):
            validate_color_hex("FF0000")

    def test_invalid_too_long(self):
        from apex_mcp.validators import validate_color_hex

        with pytest.raises(ValueError):
            validate_color_hex("#FF00001")

    def test_invalid_chars(self):
        from apex_mcp.validators import validate_color_hex

        with pytest.raises(ValueError):
            validate_color_hex("#GGHHII")


class TestValidateRegionName:
    def test_valid_name(self):
        from apex_mcp.validators import validate_region_name

        assert validate_region_name("My Region") == "My Region"

    def test_strips_whitespace(self):
        from apex_mcp.validators import validate_region_name

        assert validate_region_name("  Region  ") == "Region"

    def test_empty_raises(self):
        from apex_mcp.validators import validate_region_name

        with pytest.raises(ValueError):
            validate_region_name("")

    def test_whitespace_only_raises(self):
        from apex_mcp.validators import validate_region_name

        with pytest.raises(ValueError):
            validate_region_name("   ")

    def test_too_long_raises(self):
        from apex_mcp.validators import validate_region_name

        with pytest.raises(ValueError, match="too long"):
            validate_region_name("A" * 256)

    def test_max_length_ok(self):
        from apex_mcp.validators import validate_region_name

        name = "A" * 255
        assert validate_region_name(name) == name


class TestValidateSqlQuery:
    def test_select_ok(self):
        from apex_mcp.validators import validate_sql_query

        assert validate_sql_query("SELECT 1 FROM DUAL") == "SELECT 1 FROM DUAL"

    def test_with_ok(self):
        from apex_mcp.validators import validate_sql_query

        sql = "WITH cte AS (SELECT 1 FROM DUAL) SELECT * FROM cte"
        assert validate_sql_query(sql) == sql

    def test_case_insensitive(self):
        from apex_mcp.validators import validate_sql_query

        assert validate_sql_query("  select 1 from dual  ") == "select 1 from dual"

    def test_insert_raises(self):
        from apex_mcp.validators import validate_sql_query

        with pytest.raises(ValueError, match="must start with SELECT"):
            validate_sql_query("INSERT INTO t VALUES (1)")

    def test_empty_raises(self):
        from apex_mcp.validators import validate_sql_query

        with pytest.raises(ValueError):
            validate_sql_query("")

    def test_none_raises(self):
        from apex_mcp.validators import validate_sql_query

        with pytest.raises(ValueError):
            validate_sql_query(None)  # type: ignore[arg-type]


class TestValidateTableName:
    def test_valid_names(self):
        from apex_mcp.validators import validate_table_name

        assert validate_table_name("MY_TABLE") == "MY_TABLE"
        assert validate_table_name("table1") == "TABLE1"
        assert validate_table_name("T$X") == "T$X"
        assert validate_table_name("T#X") == "T#X"

    def test_case_normalization(self):
        from apex_mcp.validators import validate_table_name

        assert validate_table_name("my_table") == "MY_TABLE"

    def test_starts_with_digit_raises(self):
        from apex_mcp.validators import validate_table_name

        with pytest.raises(ValueError, match="not a valid Oracle identifier"):
            validate_table_name("1TABLE")

    def test_special_chars_raise(self):
        from apex_mcp.validators import validate_table_name

        with pytest.raises(ValueError):
            validate_table_name("my table")

    def test_injection_raises(self):
        from apex_mcp.validators import validate_table_name

        with pytest.raises(ValueError):
            validate_table_name("t; DROP TABLE x--")


class TestValidatePageId:
    def test_boundaries(self):
        from apex_mcp.validators import validate_page_id

        assert validate_page_id(0) == 0
        assert validate_page_id(99999) == 99999

    def test_over_max_raises(self):
        from apex_mcp.validators import validate_page_id

        with pytest.raises(ValueError):
            validate_page_id(100000)

    def test_float_raises(self):
        from apex_mcp.validators import validate_page_id

        with pytest.raises((ValueError, TypeError)):
            validate_page_id(1.5)  # type: ignore[arg-type]


class TestValidateAppId:
    def test_boundaries(self):
        from apex_mcp.validators import validate_app_id

        assert validate_app_id(100) == 100
        assert validate_app_id(999999) == 999999

    def test_below_min_raises(self):
        from apex_mcp.validators import validate_app_id

        with pytest.raises(ValueError):
            validate_app_id(99)

    def test_above_max_raises(self):
        from apex_mcp.validators import validate_app_id

        with pytest.raises(ValueError):
            validate_app_id(1000000)


class TestSafeValidate:
    def test_returns_value_on_success(self):
        from apex_mcp.validators import safe_validate, validate_page_id

        assert safe_validate(validate_page_id, 10) == 10

    def test_returns_default_on_failure(self):
        from apex_mcp.validators import safe_validate, validate_page_id

        assert safe_validate(validate_page_id, -1, default=0) == 0

    def test_returns_none_on_failure_without_default(self):
        from apex_mcp.validators import safe_validate, validate_page_id

        assert safe_validate(validate_page_id, -1) is None


class TestFrozenSets:
    def test_valid_chart_types_is_frozenset(self):
        from apex_mcp.validators import VALID_CHART_TYPES

        assert isinstance(VALID_CHART_TYPES, frozenset)

    def test_valid_item_types_is_frozenset(self):
        from apex_mcp.validators import VALID_ITEM_TYPES

        assert isinstance(VALID_ITEM_TYPES, frozenset)

    def test_valid_region_types_is_frozenset(self):
        from apex_mcp.validators import VALID_REGION_TYPES

        assert isinstance(VALID_REGION_TYPES, frozenset)

    def test_valid_display_as_is_frozenset(self):
        from apex_mcp.validators import VALID_DISPLAY_AS

        assert isinstance(VALID_DISPLAY_AS, frozenset)
