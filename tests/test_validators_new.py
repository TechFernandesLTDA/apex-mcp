"""Tests for new validator functions."""
from __future__ import annotations

import pytest
from apex_mcp.validators import (
    validate_item_name,
    validate_process_name,
    validate_auth_scheme_name,
    validate_color_hex,
    validate_sequence,
    validate_lov_query,
)


class TestValidateItemName:
    def test_valid_names(self):
        assert validate_item_name("P10_STATUS") == "P10_STATUS"
        assert validate_item_name("P1_FIRST_NAME") == "P1_FIRST_NAME"
        assert validate_item_name("p20_id") == "P20_ID"  # case normalization

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_item_name("")

    def test_no_page_prefix_raises(self):
        with pytest.raises(ValueError, match="Must match"):
            validate_item_name("STATUS")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Must match"):
            validate_item_name("P10-STATUS")


class TestValidateProcessName:
    def test_valid_name(self):
        assert validate_process_name("Save Record") == "Save Record"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_process_name("")

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="too long"):
            validate_process_name("x" * 256)


class TestValidateAuthSchemeName:
    def test_valid_name(self):
        assert validate_auth_scheme_name("IS_ADMIN") == "IS_ADMIN"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_auth_scheme_name("")


class TestValidateColorHex:
    def test_valid_colors(self):
        assert validate_color_hex("#1E88E5") == "#1E88E5"
        assert validate_color_hex("#fff") == "#FFF"  # original uppercases
        assert validate_color_hex("#FF9800") == "#FF9800"

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            validate_color_hex("red")

    def test_no_hash_raises(self):
        with pytest.raises(ValueError, match="Invalid hex color"):
            validate_color_hex("1E88E5")


class TestValidateSequence:
    def test_valid(self):
        assert validate_sequence(10) == 10
        assert validate_sequence(1) == 1

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            validate_sequence(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            validate_sequence(-1)

    def test_too_large_raises(self):
        with pytest.raises(ValueError):
            validate_sequence(100000)

    def test_float_raises(self):
        with pytest.raises(ValueError, match="must be"):
            validate_sequence(10.5)


class TestValidateLovQuery:
    def test_valid(self):
        assert validate_lov_query("SELECT name d, id r FROM statuses") is not None

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_lov_query("")

    def test_non_select_raises(self):
        with pytest.raises(ValueError, match="must start with SELECT"):
            validate_lov_query("DELETE FROM statuses")
