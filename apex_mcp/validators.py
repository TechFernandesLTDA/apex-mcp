"""Input validation helpers for apex-mcp tools.

All validators raise ValueError with a descriptive message on failure,
or return the (possibly normalized) value on success.
"""
from __future__ import annotations
import re


VALID_CHART_TYPES = {"bar", "line", "pie", "donut", "area", "scatter", "bubble",
                     "funnel", "dial", "radar", "range", "combo"}
VALID_ITEM_TYPES = {"TEXT_FIELD", "TEXTAREA", "NUMBER_FIELD", "DATE_PICKER",
                    "SELECT_LIST", "CHECKBOX", "RADIO_GROUP", "SWITCH", "HIDDEN",
                    "DISPLAY_ONLY", "FILE_BROWSE", "PASSWORD", "RICH_TEXT"}
VALID_REGION_TYPES = {"IR", "IG", "FORM", "HTML", "PLSQL", "STATIC", "CHART"}
VALID_DISPLAY_AS = {"month", "week", "day", "list"}


def validate_page_id(page_id: int) -> int:
    if not isinstance(page_id, int) or page_id < 0 or page_id > 99999:
        raise ValueError(f"page_id must be an integer between 0 and 99999, got: {page_id!r}")
    return page_id


def validate_app_id(app_id: int) -> int:
    if not isinstance(app_id, int) or app_id < 100 or app_id > 999999:
        raise ValueError(f"app_id must be an integer between 100 and 999999, got: {app_id!r}")
    return app_id


def validate_region_name(name: str) -> str:
    if not name or not isinstance(name, str) or len(name.strip()) == 0:
        raise ValueError(f"region_name must be a non-empty string, got: {name!r}")
    if len(name) > 255:
        raise ValueError(f"region_name too long (max 255 chars): {name!r}")
    return name.strip()


def validate_sql_query(sql: str) -> str:
    """Ensure sql starts with SELECT (basic check)."""
    if not sql or not isinstance(sql, str):
        raise ValueError("sql_query must be a non-empty string")
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT") and not stripped.startswith("WITH"):
        raise ValueError(
            f"sql_query must start with SELECT or WITH. Got: {sql[:60]!r}"
        )
    return sql.strip()


def validate_chart_type(chart_type: str) -> str:
    ct = chart_type.lower().strip()
    if ct not in VALID_CHART_TYPES:
        raise ValueError(
            f"chart_type '{chart_type}' is not valid. "
            f"Valid types: {sorted(VALID_CHART_TYPES)}"
        )
    return ct


def validate_item_type(item_type: str) -> str:
    it = item_type.upper().strip()
    if it not in VALID_ITEM_TYPES:
        raise ValueError(
            f"item_type '{item_type}' is not valid. "
            f"Valid types: {sorted(VALID_ITEM_TYPES)}"
        )
    return it


def validate_sequence(sequence: int) -> int:
    if not isinstance(sequence, int) or sequence < 1 or sequence > 99999:
        raise ValueError(f"sequence must be an integer between 1 and 99999, got: {sequence!r}")
    return sequence


def validate_table_name(table_name: str) -> str:
    if not table_name or not isinstance(table_name, str):
        raise ValueError("table_name must be a non-empty string")
    # Oracle identifiers: letters, digits, $, #, _ -- max 128 chars
    clean = table_name.strip().upper()
    if not re.match(r'^[A-Z][A-Z0-9_$#]{0,127}$', clean):
        raise ValueError(
            f"table_name '{table_name}' is not a valid Oracle identifier"
        )
    return clean


def validate_color_hex(color: str) -> str:
    """Validate and normalize a hex color string."""
    c = color.strip()
    if re.match(r'^#[0-9A-Fa-f]{3}$', c):
        return c.upper()
    if re.match(r'^#[0-9A-Fa-f]{6}$', c):
        return c.upper()
    raise ValueError(f"Invalid hex color: {color!r}. Expected format: #RGB or #RRGGBB")


def safe_validate(func, value, default=None):
    """Run a validator, returning default instead of raising on failure."""
    try:
        return func(value)
    except ValueError:
        return default
