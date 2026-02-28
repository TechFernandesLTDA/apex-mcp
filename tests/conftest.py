"""Pytest fixtures for apex-mcp tests.

Tests require a live Oracle ADB connection. Configure via environment variables:
    ORACLE_DB_USER, ORACLE_DB_PASS, ORACLE_DSN, ORACLE_WALLET_DIR, ORACLE_WALLET_PASSWORD
    APEX_WORKSPACE_ID, APEX_SCHEMA, APEX_WORKSPACE_NAME

Run:
    cd mcp-server
    pytest tests/ -v
    pytest tests/ -v -k "not integration"   # skip DB-dependent tests
"""
from __future__ import annotations
import os
import json
import pytest

# ── Markers ───────────────────────────────────────────────────────────────────
def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires live Oracle ADB connection")
    config.addinivalue_line("markers", "slow: long-running tests")


# ── Connection fixture ─────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def connected_db():
    """Return a connected db instance. Skip if no credentials available."""
    wallet_dir = os.getenv("ORACLE_WALLET_DIR", r"C:\Projetos\Apex\wallet")
    if not os.path.isdir(wallet_dir):
        pytest.skip("Oracle wallet not found — set ORACLE_WALLET_DIR to run integration tests")

    from apex_mcp.tools.sql_tools import apex_connect
    result_str = apex_connect()
    result = json.loads(result_str)
    if result.get("status") != "ok":
        pytest.skip(f"Could not connect to Oracle ADB: {result.get('error')}")

    from apex_mcp.db import db
    yield db


@pytest.fixture(scope="session")
def app_id():
    """Test application ID — use a high number to avoid conflicts."""
    return int(os.getenv("TEST_APP_ID", "9999"))


@pytest.fixture(autouse=True)
def reset_session():
    """Reset import session state before each test."""
    from apex_mcp.session import session
    from apex_mcp.ids import ids
    session.reset()
    ids.reset()
    yield
    session.reset()
    ids.reset()
