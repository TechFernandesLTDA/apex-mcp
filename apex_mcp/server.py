"""Oracle APEX MCP Server — Entry Point.

FastMCP server exposing tools to create, inspect, and modify Oracle APEX 24.2
applications via natural language through Claude Code.

Usage:
    python -m apex_mcp.server        # stdio mode (for MCP clients)
    python -m apex_mcp.server --help # show options
"""
from __future__ import annotations

import fastmcp
from fastmcp import FastMCP

# ── Tool imports ──────────────────────────────────────────────────────────────
from .tools.sql_tools import apex_connect, apex_run_sql, apex_status
from .tools.app_tools import (
    apex_list_apps,
    apex_create_app,
    apex_finalize_app,
    apex_delete_app,
    apex_export_app,
    apex_describe_page,
    apex_dry_run_preview,
)
from .tools.page_tools import apex_add_page, apex_list_pages
from .tools.component_tools import (
    apex_add_region,
    apex_add_item,
    apex_add_button,
    apex_add_process,
    apex_add_dynamic_action,
)
from .tools.shared_tools import (
    apex_add_lov,
    apex_add_auth_scheme,
    apex_add_nav_item,
    apex_add_app_item,
    apex_add_app_process,
)
from .tools.schema_tools import apex_list_tables, apex_describe_table
from .tools.generator_tools import (
    apex_generate_crud,
    apex_generate_dashboard,
    apex_generate_login,
)
from .tools.user_tools import apex_create_user, apex_list_users
from .tools.js_tools import (
    apex_add_page_js,
    apex_add_global_js,
    apex_generate_ajax_handler,
)
from .tools.inspect_tools import (
    apex_get_app_details,
    apex_get_page_details,
    apex_list_regions,
    apex_list_items,
    apex_list_processes,
    apex_list_dynamic_actions,
    apex_list_lovs,
    apex_list_auth_schemes,
    apex_update_region,
    apex_update_item,
    apex_delete_page,
    apex_delete_region,
    apex_copy_page,
    apex_diff_app,
)
from .tools.setup_tools import (
    apex_setup_guide,
    apex_check_requirements,
    apex_check_permissions,
    apex_fix_permissions,
)
from .tools.validation_tools import apex_add_item_validation, apex_add_item_computation
from .tools.visual_tools import (
    apex_add_jet_chart,
    apex_add_gauge,
    apex_add_funnel,
    apex_add_sparkline,
    apex_add_metric_cards,
    apex_generate_analytics_page,
)
from .tools.advanced_tools import (
    apex_generate_report_page,
    apex_generate_wizard,
    apex_add_notification_region,
    apex_add_page_css,
    apex_add_interactive_grid,
    apex_bulk_add_items,
    apex_validate_app,
    apex_preview_page,
    apex_add_search_bar,
    apex_generate_from_schema,
)

# ── Server definition ─────────────────────────────────────────────────────────
mcp = FastMCP(
    name="apex-mcp",
    instructions="""
You are connected to an Oracle APEX 24.2 development environment via MCP.

## Getting Started
1. Call `apex_setup_guide()` to see full setup requirements and instructions.
2. Call `apex_connect()` to establish the database connection.
3. Call `apex_check_requirements()` to verify everything is configured correctly.
4. Call `apex_status()` to check current session state at any time.

## Creating a New Application
```
apex_connect()
apex_create_app(app_id=200, app_name="My App")
apex_generate_login(page_id=101)
apex_add_page(1, "Dashboard", "blank")
apex_generate_dashboard(page_id=1)
apex_list_tables()                          -- discover your tables
apex_generate_crud("MY_TABLE", 10, 11)     -- full CRUD for a table
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("My Records", 10, 20, "fa-table")
apex_finalize_app()
```

## Inspecting & Editing Existing Apps
```
apex_list_apps()                            -- see all apps
apex_get_app_details(200)                  -- full app metadata
apex_get_page_details(200, 10)             -- all components on a page
apex_list_regions(200, 10)                 -- regions on a page
apex_list_items(200, 10)                   -- items on a page
apex_update_region(200, 10, "My Region", new_source_sql="SELECT * FROM v2_table")
apex_update_item(200, 10, "P10_STATUS", new_lov_definition="SELECT name d, id r FROM statuses")
```

## JavaScript Development
```
apex_add_page_js(10, "function myHelper() { apex.message.showPageSuccess('Done!'); }")
apex_generate_ajax_handler(10, "SEARCH_DATA",
    "SELECT * FROM my_table WHERE name LIKE :P10_SEARCH || '%'")
apex_add_dynamic_action(10, "On Search Click", "click", "P10_SEARCH_BTN",
    "execute_javascript", "searchData();")
```

## Modern Analytics & Visualizations
```
# Full analytics page (metrics + charts) in one call:
apex_generate_analytics_page(
    page_id=5, page_name="Analytics",
    metrics=[
        {"label": "Total", "sql": "SELECT COUNT(*) FROM MY_TABLE", "icon": "fa-database", "color": "#1E88E5"},
    ],
    charts=[
        {"region_name": "By Status", "chart_type": "pie",
         "sql_query": "SELECT STATUS LABEL, COUNT(*) VALUE FROM MY_TABLE GROUP BY STATUS",
         "color_palette": ["#1E88E5","#43A047","#FF9800"]},
        {"region_name": "Monthly Trend", "chart_type": "line",
         "sql_query": "SELECT TO_CHAR(CREATED,'MM/YYYY') LABEL, COUNT(*) VALUE FROM MY_TABLE GROUP BY TO_CHAR(CREATED,'MM/YYYY') ORDER BY 1"},
    ]
)

# Individual chart types:
apex_add_jet_chart(page_id=5, region_name="Trend", chart_type="bar",
    sql_query="SELECT col1 LABEL, col2 VALUE FROM my_table ORDER BY 1",
    color_palette=["#1E88E5","#43A047","#FF9800"])
apex_add_gauge(page_id=5, region_name="Score", sql_query="SELECT 72 VALUE FROM DUAL",
    value_column="VALUE", min_value=0, max_value=100, thresholds=[33,66])
apex_add_funnel(page_id=5, region_name="Pipeline",
    sql_query="SELECT STAGE LABEL, CNT VALUE FROM PIPELINE ORDER BY SEQ",
    label_column="LABEL", value_column="VALUE")
apex_add_sparkline(page_id=5, region_name="KPIs",
    metrics=[{"label": "Active", "sql": "SELECT 42 FROM DUAL", "trend_sql": "SELECT VAL FROM T ORDER BY DT",
               "color": "#43A047"}])
apex_add_metric_cards(page_id=5, region_name="KPIs", style="gradient", metrics=[...])
```

## Advanced Page Generators
```
# IR page with optional filter items:
apex_generate_report_page(page_id=10, page_name="Orders",
    sql_query="SELECT * FROM ORDERS", filter_items=["STATUS","CUSTOMER_ID"])

# Multi-step wizard:
apex_generate_wizard(start_page_id=50, steps=[
    {"title": "Basic Info", "items": [{"name": "NOME", "type": "TEXT"}, ...]},
    {"title": "Details",    "items": [{"name": "DESC",  "type": "TEXTAREA"}]},
], wizard_title="New Record", finish_redirect_page=10)

# Interactive Grid (editable spreadsheet):
apex_add_interactive_grid(page_id=20, region_name="Orders",
    table_name="ORDERS", editable=True, add_row=True)

# Bulk item creation:
apex_bulk_add_items(page_id=10, region_name="Filters",
    items=[{"name":"STATUS","type":"SELECT","lov":"SELECT s,v FROM ..."},
           {"name":"DATE_FROM","type":"DATE_PICKER"}])

# Notification / alert region:
apex_add_notification_region(page_id=5, region_name="Notice",
    message="Beta feature", notification_type="warning", dismissible=True)

# Schema-to-app generator:
apex_generate_from_schema(tables=["ORDERS","CUSTOMERS","PRODUCTS"],
    start_page_id=10, include_dashboard=True)

# App health check:
apex_validate_app()   -- returns score 0-100 + issues list

# Dry-run preview (test without executing):
apex_dry_run_preview(enabled=True)
# ... build calls ...
apex_dry_run_preview(enabled=False)  -- returns PL/SQL log
```

## Key Conventions (APEX Best Practices)
- Item names: P{page_id}_{COLUMN_NAME} (auto-applied)
- AJAX callbacks: UPPERCASE names
- Navigation: sequences in multiples of 10
- Authorization schemes: IS_ prefix (IS_ADMIN, IS_MANAGER)
- Always call apex_finalize_app() when done creating/modifying

## After Creating an App
Access it at: f?p={app_id}  (relative to your APEX base URL)
""",
)

# ── Register all tools ────────────────────────────────────────────────────────

# Setup & diagnostics
mcp.tool()(apex_setup_guide)
mcp.tool()(apex_check_requirements)
mcp.tool()(apex_check_permissions)
mcp.tool()(apex_fix_permissions)

# Connection & session
mcp.tool()(apex_connect)
mcp.tool()(apex_run_sql)
mcp.tool()(apex_status)

# App lifecycle
mcp.tool()(apex_list_apps)
mcp.tool()(apex_create_app)
mcp.tool()(apex_finalize_app)
mcp.tool()(apex_delete_app)
mcp.tool()(apex_export_app)
mcp.tool()(apex_describe_page)
mcp.tool()(apex_dry_run_preview)

# Pages
mcp.tool()(apex_add_page)
mcp.tool()(apex_list_pages)

# Components
mcp.tool()(apex_add_region)
mcp.tool()(apex_add_item)
mcp.tool()(apex_add_button)
mcp.tool()(apex_add_process)
mcp.tool()(apex_add_dynamic_action)

# Shared components
mcp.tool()(apex_add_lov)
mcp.tool()(apex_add_auth_scheme)
mcp.tool()(apex_add_nav_item)
mcp.tool()(apex_add_app_item)
mcp.tool()(apex_add_app_process)

# Schema introspection
mcp.tool()(apex_list_tables)
mcp.tool()(apex_describe_table)

# Generators (high-level)
mcp.tool()(apex_generate_crud)
mcp.tool()(apex_generate_dashboard)
mcp.tool()(apex_generate_login)

# User management
mcp.tool()(apex_create_user)
mcp.tool()(apex_list_users)

# JavaScript
mcp.tool()(apex_add_page_js)
mcp.tool()(apex_add_global_js)
mcp.tool()(apex_generate_ajax_handler)

# Inspection & editing of existing apps
mcp.tool()(apex_get_app_details)
mcp.tool()(apex_get_page_details)
mcp.tool()(apex_list_regions)
mcp.tool()(apex_list_items)
mcp.tool()(apex_list_processes)
mcp.tool()(apex_list_dynamic_actions)
mcp.tool()(apex_list_lovs)
mcp.tool()(apex_list_auth_schemes)
mcp.tool()(apex_update_region)
mcp.tool()(apex_update_item)
mcp.tool()(apex_delete_page)
mcp.tool()(apex_delete_region)
mcp.tool()(apex_copy_page)
mcp.tool()(apex_diff_app)

# Validations & computations
mcp.tool()(apex_add_item_validation)
mcp.tool()(apex_add_item_computation)

# Visual tools (JET charts + metric cards + gauges + sparklines)
mcp.tool()(apex_add_jet_chart)
mcp.tool()(apex_add_gauge)
mcp.tool()(apex_add_funnel)
mcp.tool()(apex_add_sparkline)
mcp.tool()(apex_add_metric_cards)
mcp.tool()(apex_generate_analytics_page)

# Advanced generators & utilities
mcp.tool()(apex_generate_report_page)
mcp.tool()(apex_generate_wizard)
mcp.tool()(apex_add_notification_region)
mcp.tool()(apex_add_page_css)
mcp.tool()(apex_add_interactive_grid)
mcp.tool()(apex_bulk_add_items)
mcp.tool()(apex_validate_app)
mcp.tool()(apex_preview_page)
mcp.tool()(apex_add_search_bar)
mcp.tool()(apex_generate_from_schema)


def main():
    """Entry point for stdio MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
