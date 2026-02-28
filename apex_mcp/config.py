"""Configuration constants for Oracle APEX MCP Server."""
import os

# Oracle ADB connection defaults (all required — set via env vars or .mcp.json)
DB_USER     = os.getenv("ORACLE_DB_USER", "")
DB_PASS     = os.getenv("ORACLE_DB_PASS", "")
DB_DSN      = os.getenv("ORACLE_DSN", "")
WALLET_DIR  = os.getenv("ORACLE_WALLET_DIR", "")
WALLET_PASS = os.getenv("ORACLE_WALLET_PASSWORD", "")

# APEX Workspace
WORKSPACE_ID   = int(os.getenv("APEX_WORKSPACE_ID", "0"))
WORKSPACE_NAME = os.getenv("APEX_WORKSPACE_NAME", "")
APEX_SCHEMA    = os.getenv("APEX_SCHEMA", "")

# APEX version
APEX_VERSION          = "24.2.13"
APEX_RELEASE          = "24.2.13"
APEX_VERSION_DATE     = "2024.11.30"
APEX_COMPAT_MODE      = "24.2"

# Default app settings
DEFAULT_DATE_FORMAT      = "DD/MM/YYYY"
DEFAULT_TIMESTAMP_FORMAT = "DD/MM/YYYY HH24:MI"
DEFAULT_LANGUAGE         = "pt-br"
