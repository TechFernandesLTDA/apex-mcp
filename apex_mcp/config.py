"""Configuration constants for Oracle APEX MCP Server."""
import os

# Oracle ADB connection defaults
DB_USER     = os.getenv("ORACLE_DB_USER", "TEA_APP")
DB_PASS     = os.getenv("ORACLE_DB_PASS", "TeaApp@2024#Unimed")
DB_DSN      = os.getenv("ORACLE_DSN", "u5cvlivnjuodscai_tp")
WALLET_DIR  = os.getenv("ORACLE_WALLET_DIR", r"C:\Projetos\Apex\wallet")
WALLET_PASS = os.getenv("ORACLE_WALLET_PASSWORD", "apex1234")

# APEX Workspace
WORKSPACE_ID   = int(os.getenv("APEX_WORKSPACE_ID", "8822816515098715"))
WORKSPACE_NAME = os.getenv("APEX_WORKSPACE_NAME", "TEA")
APEX_SCHEMA    = os.getenv("APEX_SCHEMA", "TEA_APP")

# APEX version
APEX_VERSION          = "24.2.13"
APEX_RELEASE          = "24.2.13"
APEX_VERSION_DATE     = "2024.11.30"
APEX_COMPAT_MODE      = "24.2"

# Default app settings
DEFAULT_DATE_FORMAT      = "DD/MM/YYYY"
DEFAULT_TIMESTAMP_FORMAT = "DD/MM/YYYY HH24:MI"
DEFAULT_LANGUAGE         = "pt-br"
