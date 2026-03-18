"""Tests for MCP resources and prompts."""
from __future__ import annotations

import asyncio
import json
import pytest


def test_resource_config_returns_json():
    """Test apex://config resource returns valid JSON."""
    from apex_mcp.server import resource_config
    result = resource_config()
    data = json.loads(result)
    assert "connected" in data
    assert "apex_version" in data


def test_resource_session_returns_json():
    """Test apex://session resource returns valid JSON."""
    from apex_mcp.server import resource_session
    result = resource_session()
    data = json.loads(result)
    assert "app_id" in data
    assert "pages" in data


def test_resource_tables_not_connected():
    """Test apex://schema/tables returns error when not connected."""
    from apex_mcp.server import resource_tables
    result = resource_tables()
    data = json.loads(result)
    assert "error" in data


def test_resource_apps_not_connected():
    """Test apex://apps returns error when not connected."""
    from apex_mcp.server import resource_apps
    result = resource_apps()
    data = json.loads(result)
    assert "error" in data


def test_prompt_create_crud_app():
    """Test create_crud_app prompt returns workflow string."""
    from apex_mcp.server import create_crud_app
    result = create_crud_app(table_name="ORDERS", app_id=200, app_name="My App")
    assert "ORDERS" in result
    assert "apex_connect" in result
    assert "apex_generate_crud" in result


def test_prompt_create_dashboard_app():
    """Test create_dashboard_app prompt returns workflow string."""
    from apex_mcp.server import create_dashboard_app
    result = create_dashboard_app(app_id=300, app_name="Dashboard")
    assert "apex_list_tables" in result
    assert "apex_add_metric_cards" in result


def test_prompt_create_full_app_from_schema():
    """Test create_full_app_from_schema prompt returns workflow."""
    from apex_mcp.server import create_full_app_from_schema
    result = create_full_app_from_schema()
    assert "apex_generate_from_schema" in result


def test_prompt_inspect_existing_app():
    """Test inspect_existing_app prompt returns workflow."""
    from apex_mcp.server import inspect_existing_app
    result = inspect_existing_app(app_id=200)
    assert "200" in result
    assert "apex_get_app_details" in result


def test_prompt_add_rest_api():
    """Test add_rest_api prompt returns workflow."""
    from apex_mcp.server import add_rest_api
    result = add_rest_api(table_name="ORDERS")
    assert "ORDERS" in result
    assert "apex_generate_rest_endpoints" in result
