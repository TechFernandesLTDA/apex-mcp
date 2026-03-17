"""Configuration constants for Oracle APEX MCP Server.

All values are read from environment variables at import time.  Missing
variables emit a ``RuntimeWarning`` but do not prevent the module from
loading -- this allows unit tests to run without a full Oracle setup.
"""
from __future__ import annotations

import os
import warnings

# Oracle ADB connection defaults (all required -- set via env vars or .mcp.json)
DB_USER: str = os.getenv("ORACLE_DB_USER", "")
DB_PASS: str = os.getenv("ORACLE_DB_PASS", "")
DB_DSN: str = os.getenv("ORACLE_DSN", "")
WALLET_DIR: str = os.getenv("ORACLE_WALLET_DIR", "")
WALLET_PASS: str = os.getenv("ORACLE_WALLET_PASSWORD", "")

# APEX Workspace
_ws_id_str: str = os.getenv("APEX_WORKSPACE_ID", "0")
try:
    WORKSPACE_ID: int = int(_ws_id_str)
except ValueError:
    WORKSPACE_ID = 0
WORKSPACE_NAME: str = os.getenv("APEX_WORKSPACE_NAME", "")
APEX_SCHEMA: str = os.getenv("APEX_SCHEMA", "")

# APEX version
APEX_VERSION: str = "24.2.13"
APEX_RELEASE: str = "24.2.13"
APEX_VERSION_DATE: str = "2024.11.30"
APEX_COMPAT_MODE: str = "24.2"

# Default app settings
DEFAULT_DATE_FORMAT: str = "DD/MM/YYYY"
DEFAULT_TIMESTAMP_FORMAT: str = "DD/MM/YYYY HH24:MI"
DEFAULT_LANGUAGE: str = "pt-br"

_REQUIRED_VARS: dict[str, str] = {
    "ORACLE_DB_USER": DB_USER,
    "ORACLE_DB_PASS": DB_PASS,
    "ORACLE_DSN": DB_DSN,
    "ORACLE_WALLET_DIR": WALLET_DIR,
    "APEX_WORKSPACE_ID": _ws_id_str,
    "APEX_SCHEMA": APEX_SCHEMA,
    "APEX_WORKSPACE_NAME": WORKSPACE_NAME,
}
_missing: list[str] = [k for k, v in _REQUIRED_VARS.items() if not v or v == "0"]
if _missing:
    warnings.warn(
        f"apex-mcp: missing required env vars: {', '.join(_missing)}. "
        "Set them in .mcp.json or as environment variables.",
        RuntimeWarning,
        stacklevel=2,
    )
