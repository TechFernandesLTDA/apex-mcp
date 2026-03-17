"""Shared utility helpers for apex-mcp tools."""
from __future__ import annotations

import json
from typing import Any


def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals.

    Doubles every ``'`` so that ``O'Brien`` becomes ``O''Brien`` inside
    a PL/SQL ``'...'`` literal.

    Args:
        value: The raw string to escape.

    Returns:
        The escaped string safe for PL/SQL embedding.
    """
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL ``begin ... end;`` block.

    Args:
        sql: One or more PL/SQL statements (without the surrounding block).

    Returns:
        A complete anonymous block string.
    """
    return f"begin\n{sql}\nend;"


def _json(obj: Any) -> str:
    """Serialize *obj* to a JSON string with consistent formatting.

    Uses ``ensure_ascii=False`` so non-ASCII characters (e.g. Portuguese
    accents) are preserved, ``indent=2`` for readability, and ``default=str``
    as a fallback serializer for types like ``datetime.date``.

    Args:
        obj: Any JSON-serializable object (dict, list, scalar, etc.).

    Returns:
        A pretty-printed JSON string.
    """
    return json.dumps(obj, ensure_ascii=False, indent=2, default=str)


def _sql_to_varchar2(sql: str) -> str:
    """Convert multi-line SQL/PL/SQL to a ``wwv_flow_string.join(...)`` expression.

    APEX import scripts represent long SQL strings as a call to
    ``wwv_flow_string.join(wwv_flow_t_varchar2(...))`` with each source line
    as a separate element.  This helper performs that conversion, escaping
    single quotes along the way.

    Args:
        sql: The raw SQL or PL/SQL text (may be multi-line).

    Returns:
        A PL/SQL expression suitable for embedding in ``p_plug_source`` or
        similar parameters.  Returns ``''`` for empty input.
    """
    lines = sql.replace("'", "''").splitlines()
    if not lines:
        return "''"
    quoted = [f"'{line}'" for line in lines]
    return "wwv_flow_string.join(wwv_flow_t_varchar2(\n" + ",\n".join(quoted) + "))"
