"""Shared utility helpers for apex-mcp tools."""
from __future__ import annotations


def _esc(value: str) -> str:
    """Escape single quotes for safe embedding in PL/SQL string literals."""
    return value.replace("'", "''")


def _blk(sql: str) -> str:
    """Wrap SQL in an anonymous PL/SQL begin...end; block."""
    return f"begin\n{sql}\nend;"


def _sql_to_varchar2(sql: str) -> str:
    """Convert multi-line SQL/PLSQL to wwv_flow_string.join(wwv_flow_t_varchar2(...))."""
    lines = sql.replace("'", "''").splitlines()
    if not lines:
        return "''"
    quoted = [f"'{line}'" for line in lines]
    return "wwv_flow_string.join(wwv_flow_t_varchar2(\n" + ",\n".join(quoted) + "))"
