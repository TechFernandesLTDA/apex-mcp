"""Oracle APEX MCP Server — Entry Point.

FastMCP server exposing tools to create, inspect, and modify Oracle APEX 24.2
applications via natural language. Supports Claude, GPT, Gemini, Cursor, VS Code,
and any MCP-compatible AI client.

Usage:
    python -m apex_mcp                                    # stdio (default)
    python -m apex_mcp --transport streamable-http        # HTTP on 127.0.0.1:8000
    python -m apex_mcp --transport sse --port 9000        # SSE on port 9000
    apex-mcp --help                                       # show all options

Environment variable overrides (lower priority than CLI flags):
    MCP_TRANSPORT   stdio | streamable-http | sse
    MCP_HOST        default 127.0.0.1
    MCP_PORT        default 8000
    MCP_PATH        endpoint path (streamable-http: /mcp, sse: /sse)
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")

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
    apex_undo_last,
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
from .tools.schema_tools import apex_list_tables, apex_describe_table, apex_detect_relationships
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
    apex_delete_item,
    apex_delete_button,
    apex_update_page,
    apex_copy_page,
    apex_diff_app,
)
from .tools.setup_tools import (
    apex_setup_guide,
    apex_check_requirements,
    apex_check_permissions,
    apex_fix_permissions,
    apex_refresh_templates,
    apex_health_check,
    apex_get_audit_log,
)
from .tools.validation_tools import apex_add_item_validation, apex_add_item_computation
from .tools.visual_tools import (
    apex_add_jet_chart,
    apex_add_gauge,
    apex_add_funnel,
    apex_add_sparkline,
    apex_add_metric_cards,
    apex_add_calendar,
    apex_generate_analytics_page,
)
from .tools.devops_tools import (
    apex_generate_rest_endpoints,
    apex_export_page,
    apex_generate_docs,
    apex_begin_batch,
    apex_commit_batch,
)
from .tools.advanced_tools import (
    apex_generate_report_page,
    apex_generate_wizard,
    apex_add_notification_region,
    apex_add_page_css,
    apex_add_global_css,
    apex_add_interactive_grid,
    apex_bulk_add_items,
    apex_validate_app,
    apex_preview_page,
    apex_add_search_bar,
    apex_generate_from_schema,
    apex_generate_modal_form,
    apex_add_master_detail,
    apex_add_timeline,
    apex_add_breadcrumb,
    apex_add_faceted_search,
    apex_add_chart_drilldown,
    apex_add_file_upload,
)
from .tools.ui_tools import (
    apex_add_hero_banner,
    apex_add_kpi_row,
    apex_add_progress_tracker,
    apex_add_alert_box,
    apex_add_stat_delta,
    apex_add_quick_links,
    apex_add_leaderboard,
    apex_add_tag_cloud,
    apex_add_percent_bars,
    apex_add_icon_list,
    apex_add_traffic_light,
    apex_add_spotlight_metric,
    apex_add_comparison_panel,
    apex_add_activity_stream,
    apex_add_status_matrix,
    apex_add_collapsible_region,
    apex_add_tabs_container,
    apex_add_data_card_grid,
    apex_add_heatmap_grid,
    apex_add_ribbon_stats,
)
from .tools.chart_tools import (
    apex_add_stacked_chart,
    apex_add_combo_chart,
    apex_add_pareto_chart,
    apex_add_scatter_plot,
    apex_add_range_chart,
    apex_add_area_chart,
    apex_add_animated_counter,
    apex_add_gradient_donut,
    apex_add_mini_charts_row,
    apex_add_bubble_chart,
)

# ── Lifespan handler ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(server):
    """Manage server lifecycle — cleanup DB connections on shutdown."""
    logging.getLogger("apex_mcp.server").info("apex-mcp starting")
    yield
    # Cleanup on shutdown
    from .db import db
    if db.is_connected():
        try:
            db._conn.close()
            db._conn = None
        except Exception:
            pass
    logging.getLogger("apex_mcp.server").info("apex-mcp stopped")


# ── Server definition ─────────────────────────────────────────────────────────
mcp = FastMCP(
    name="apex-mcp",
    lifespan=lifespan,
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

## New UX Components
```
# Modal popup form (no separate page):
apex_generate_modal_form(page_id=10, region_name="Edit Order", table_name="ORDERS", pk_item_name="ID")

# Master-detail (two IRs, detail filtered by master selection):
apex_add_master_detail(page_id=20, master_region_name="Clinics", master_sql="SELECT * FROM TEA_CLINICAS",
    detail_region_name="Therapists", detail_sql="SELECT * FROM TEA_TERAPEUTAS WHERE ID_CLINICA = :P20_SELECTED_ID",
    link_column="ID_CLINICA", page_item_name="SELECTED_ID")

# Timeline (audit trail, history):
apex_add_timeline(page_id=5, region_name="History", sql_query="SELECT DT, TITLE, BODY FROM LOG ORDER BY DT DESC",
    date_col="DT", title_col="TITLE", body_col="BODY")

# Calendar (DATE column):
apex_add_calendar(page_id=5, region_name="Schedule",
    sql_query="SELECT DT_AGENDADO, DS_OBSERVACAO FROM TEA_AVALIACOES",
    date_column="DT_AGENDADO", title_column="DS_OBSERVACAO", display_as="month")

# Faceted search (filter sidebar + IR):
apex_add_faceted_search(page_id=10, region_name="Patients",
    sql_query="SELECT * FROM TEA_BENEFICIARIOS",
    facets=[{"column":"DS_SEXO","label":"Gender"},{"column":"ID_CLINICA","label":"Clinic"}])

# Chart drilldown (click chart → filter IR):
apex_add_chart_drilldown(page_id=5, chart_region_name="By Status",
    target_item_name="FILTER_STATUS", filter_column="STATUS", target_region_name="Records List")

# File upload (BLOB storage):
apex_add_file_upload(page_id=11, region_name="Documents", item_name="ATTACHMENT",
    table_name="DOCUMENTS", pk_item="P11_ID", blob_col="CONTENT",
    filename_col="FILENAME", mimetype_col="MIME_TYPE")
```

## DevOps Tools
```
# ORDS REST endpoints for a table:
apex_generate_rest_endpoints("ORDERS", base_path="orders", require_auth=True)
# → GET/POST /ords/schema/orders/   GET/PUT/DELETE /ords/schema/orders/:id

# Export a single page as SQL:
apex_export_page(app_id=200, page_id=10, output_path="C:/exports/p10.sql")

# Auto-generate Markdown docs for an app:
apex_generate_docs(app_id=200)  -- returns full Markdown

# Batch mode (queue operations, 1 DB round-trip):
apex_begin_batch()
apex_add_region(...)
apex_add_item(...)
apex_add_button(...)
apex_commit_batch()  -- executes all at once

# Detect FK relationships between tables:
apex_detect_relationships(["ORDERS","CUSTOMERS","PRODUCTS"])
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

# ── Tool annotations ─────────────────────────────────────────────────────────
_READ = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_READ_OPEN = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
_SAFE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
_DELETE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}

# ── Register all tools ────────────────────────────────────────────────────────

# Setup & diagnostics
mcp.tool(annotations=_READ, tags={"setup"})(apex_setup_guide)
mcp.tool(annotations=_READ, tags={"setup"})(apex_check_requirements)
mcp.tool(annotations=_READ, tags={"setup"})(apex_check_permissions)
mcp.tool(annotations=_SAFE, tags={"setup"})(apex_fix_permissions)
mcp.tool(annotations=_SAFE, tags={"setup"})(apex_refresh_templates)
mcp.tool(annotations=_READ, tags={"setup"})(apex_health_check)
mcp.tool(annotations=_READ, tags={"setup"})(apex_get_audit_log)

# Connection & session
mcp.tool(annotations=_SAFE, tags={"connection"})(apex_connect)
mcp.tool(annotations=_READ_OPEN, tags={"connection"})(apex_run_sql)
mcp.tool(annotations=_READ, tags={"connection"})(apex_status)

# App lifecycle
mcp.tool(annotations=_READ, tags={"app"})(apex_list_apps)
mcp.tool(annotations=_WRITE, tags={"app"})(apex_create_app)
mcp.tool(annotations=_WRITE, tags={"app"})(apex_finalize_app)
mcp.tool(annotations=_DELETE, tags={"app"})(apex_delete_app)
mcp.tool(annotations=_READ, tags={"app"})(apex_export_app)
mcp.tool(annotations=_READ, tags={"app"})(apex_describe_page)
mcp.tool(annotations=_SAFE, tags={"app"})(apex_dry_run_preview)
mcp.tool(annotations=_DELETE, tags={"app"})(apex_undo_last)

# Pages
mcp.tool(annotations=_WRITE, tags={"page"})(apex_add_page)
mcp.tool(annotations=_READ, tags={"page"})(apex_list_pages)

# Components
mcp.tool(annotations=_WRITE, tags={"component"})(apex_add_region)
mcp.tool(annotations=_WRITE, tags={"component"})(apex_add_item)
mcp.tool(annotations=_WRITE, tags={"component"})(apex_add_button)
mcp.tool(annotations=_WRITE, tags={"component"})(apex_add_process)
mcp.tool(annotations=_WRITE, tags={"component"})(apex_add_dynamic_action)

# Shared components
mcp.tool(annotations=_WRITE, tags={"shared"})(apex_add_lov)
mcp.tool(annotations=_WRITE, tags={"shared"})(apex_add_auth_scheme)
mcp.tool(annotations=_WRITE, tags={"shared"})(apex_add_nav_item)
mcp.tool(annotations=_WRITE, tags={"shared"})(apex_add_app_item)
mcp.tool(annotations=_WRITE, tags={"shared"})(apex_add_app_process)

# Schema introspection
mcp.tool(annotations=_READ, tags={"schema"})(apex_list_tables)
mcp.tool(annotations=_READ, tags={"schema"})(apex_describe_table)
mcp.tool(annotations=_READ, tags={"schema"})(apex_detect_relationships)

# Generators (high-level)
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_crud)
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_dashboard)
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_login)

# User management
mcp.tool(annotations=_WRITE, tags={"user"})(apex_create_user)
mcp.tool(annotations=_READ, tags={"user"})(apex_list_users)

# JavaScript
mcp.tool(annotations=_WRITE, tags={"javascript"})(apex_add_page_js)
mcp.tool(annotations=_READ, tags={"javascript"})(apex_add_global_js)
mcp.tool(annotations=_WRITE, tags={"javascript"})(apex_generate_ajax_handler)

# Inspection & editing of existing apps
mcp.tool(annotations=_READ, tags={"inspect"})(apex_get_app_details)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_get_page_details)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_regions)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_items)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_processes)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_dynamic_actions)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_lovs)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_list_auth_schemes)
mcp.tool(annotations=_WRITE, tags={"inspect"})(apex_update_region)
mcp.tool(annotations=_WRITE, tags={"inspect"})(apex_update_item)
mcp.tool(annotations=_DELETE, tags={"inspect"})(apex_delete_page)
mcp.tool(annotations=_DELETE, tags={"inspect"})(apex_delete_region)
mcp.tool(annotations=_DELETE, tags={"inspect"})(apex_delete_item)
mcp.tool(annotations=_DELETE, tags={"inspect"})(apex_delete_button)
mcp.tool(annotations=_WRITE, tags={"inspect"})(apex_update_page)
mcp.tool(annotations=_WRITE, tags={"inspect"})(apex_copy_page)
mcp.tool(annotations=_READ, tags={"inspect"})(apex_diff_app)

# Validations & computations
mcp.tool(annotations=_WRITE, tags={"validation"})(apex_add_item_validation)
mcp.tool(annotations=_WRITE, tags={"validation"})(apex_add_item_computation)

# Visual tools (JET charts + metric cards + gauges + sparklines + calendar)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_jet_chart)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_gauge)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_funnel)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_sparkline)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_metric_cards)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_add_calendar)
mcp.tool(annotations=_WRITE, tags={"visual"})(apex_generate_analytics_page)

# Advanced generators & utilities
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_report_page)
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_wizard)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_notification_region)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_page_css)
mcp.tool(annotations=_READ, tags={"advanced"})(apex_add_global_css)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_interactive_grid)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_bulk_add_items)
mcp.tool(annotations=_READ, tags={"validation"})(apex_validate_app)
mcp.tool(annotations=_READ, tags={"advanced"})(apex_preview_page)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_search_bar)
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_from_schema)

# Component tools — modal, master-detail, timeline, breadcrumb, faceted search, drilldown, file upload
mcp.tool(annotations=_WRITE, tags={"generator"})(apex_generate_modal_form)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_master_detail)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_timeline)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_breadcrumb)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_faceted_search)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_chart_drilldown)
mcp.tool(annotations=_WRITE, tags={"advanced"})(apex_add_file_upload)

# DevOps — REST endpoints, page export, docs, batch mode
mcp.tool(annotations=_WRITE, tags={"devops"})(apex_generate_rest_endpoints)
mcp.tool(annotations=_READ, tags={"devops"})(apex_export_page)
mcp.tool(annotations=_READ, tags={"devops"})(apex_generate_docs)
mcp.tool(annotations=_SAFE, tags={"devops"})(apex_begin_batch)
mcp.tool(annotations=_WRITE, tags={"devops"})(apex_commit_batch)

# UI Tools — 20 rich visual HTML components
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_hero_banner)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_kpi_row)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_progress_tracker)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_alert_box)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_stat_delta)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_quick_links)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_leaderboard)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_tag_cloud)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_percent_bars)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_icon_list)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_traffic_light)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_spotlight_metric)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_comparison_panel)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_activity_stream)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_status_matrix)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_collapsible_region)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_tabs_container)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_data_card_grid)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_heatmap_grid)
mcp.tool(annotations=_WRITE, tags={"ui"})(apex_add_ribbon_stats)

# Chart Tools — 10 advanced chart types
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_stacked_chart)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_combo_chart)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_pareto_chart)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_scatter_plot)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_range_chart)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_area_chart)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_animated_counter)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_gradient_donut)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_mini_charts_row)
mcp.tool(annotations=_WRITE, tags={"chart"})(apex_add_bubble_chart)

# ── MCP Resources ────────────────────────────────────────────────────────────

@mcp.resource("apex://config")
def resource_config() -> str:
    """Current apex-mcp configuration and connection status."""
    from .config import DB_USER, DB_DSN, APEX_SCHEMA, WORKSPACE_ID, WORKSPACE_NAME, APEX_VERSION
    from .db import db
    return json.dumps({
        "oracle_user": DB_USER,
        "oracle_dsn": DB_DSN,
        "apex_schema": APEX_SCHEMA,
        "workspace_id": WORKSPACE_ID,
        "workspace_name": WORKSPACE_NAME,
        "apex_version": APEX_VERSION,
        "connected": db.is_connected(),
    }, indent=2)


@mcp.resource("apex://session")
def resource_session() -> str:
    """Current import session state (active app, pages, components)."""
    from .session import session
    return json.dumps(session.summary(), indent=2)


@mcp.resource("apex://schema/tables")
def resource_tables() -> str:
    """List of database tables in the current schema (requires connection)."""
    from .db import db
    if not db.is_connected():
        return json.dumps({"error": "Not connected. Call apex_connect() first."})
    try:
        rows = db.execute(
            "SELECT table_name, num_rows FROM user_tables ORDER BY table_name"
        )
        return json.dumps({"tables": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("apex://schema/tables/{table_name}")
def resource_table_detail(table_name: str) -> str:
    """Detailed column metadata for a specific table."""
    from .db import db
    if not db.is_connected():
        return json.dumps({"error": "Not connected. Call apex_connect() first."})
    try:
        cols = db.execute(
            "SELECT column_name, data_type, data_length, nullable, data_default "
            "FROM user_tab_columns WHERE table_name = :t ORDER BY column_id",
            {"t": table_name.upper()}
        )
        pks = db.execute(
            "SELECT cols.column_name FROM user_constraints cons "
            "JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name "
            "WHERE cons.table_name = :t AND cons.constraint_type = 'P' "
            "ORDER BY cols.position",
            {"t": table_name.upper()}
        )
        fks = db.execute(
            "SELECT cols.column_name, r_cons.table_name AS ref_table "
            "FROM user_constraints cons "
            "JOIN user_cons_columns cols ON cons.constraint_name = cols.constraint_name "
            "JOIN user_constraints r_cons ON cons.r_constraint_name = r_cons.constraint_name "
            "WHERE cons.table_name = :t AND cons.constraint_type = 'R'",
            {"t": table_name.upper()}
        )
        return json.dumps({
            "table_name": table_name.upper(),
            "columns": cols,
            "primary_keys": [p["COLUMN_NAME"] for p in pks],
            "foreign_keys": fks,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("apex://apps")
def resource_apps() -> str:
    """List of APEX applications in the current workspace (requires connection)."""
    from .db import db
    from .config import WORKSPACE_NAME
    if not db.is_connected():
        return json.dumps({"error": "Not connected. Call apex_connect() first."})
    try:
        rows = db.execute(
            "SELECT application_id, application_name, pages, "
            "TO_CHAR(last_updated_on, 'YYYY-MM-DD HH24:MI') AS last_updated "
            "FROM apex_applications WHERE workspace = :ws ORDER BY application_id",
            {"ws": WORKSPACE_NAME}
        )
        return json.dumps({"applications": rows}, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.resource("apex://apps/{app_id}")
def resource_app_detail(app_id: int) -> str:
    """Detailed metadata for a specific APEX application."""
    from .db import db
    if not db.is_connected():
        return json.dumps({"error": "Not connected. Call apex_connect() first."})
    try:
        app = db.execute(
            "SELECT application_id, application_name, alias, pages, "
            "owner, compatibility_mode, authentication_scheme, "
            "TO_CHAR(last_updated_on, 'YYYY-MM-DD HH24:MI') AS last_updated "
            "FROM apex_applications WHERE application_id = :id",
            {"id": app_id}
        )
        pages = db.execute(
            "SELECT page_id, page_name, page_mode "
            "FROM apex_application_pages WHERE application_id = :id ORDER BY page_id",
            {"id": app_id}
        )
        return json.dumps({
            "application": app[0] if app else None,
            "pages": pages,
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── MCP Prompts ──────────────────────────────────────────────────────────────

@mcp.prompt()
def create_crud_app(table_name: str, app_id: int = 200, app_name: str = "My App") -> str:
    """Step-by-step workflow to create a full CRUD application for a database table."""
    return f"""Create a complete APEX CRUD application for the table {table_name}.

Follow these steps in order:
1. apex_connect() — establish database connection
2. apex_describe_table("{table_name}") — understand the table structure
3. apex_create_app(app_id={app_id}, app_name="{app_name}")
4. apex_generate_login(page_id=101)
5. apex_add_page(1, "Dashboard", "blank")
6. apex_generate_crud("{table_name}", 10, 11)
7. apex_add_nav_item("Dashboard", 1, 10, "fa-home")
8. apex_add_nav_item("{table_name}", 10, 20, "fa-table")
9. apex_finalize_app()

After finalization, the app will be accessible at f?p={app_id}"""


@mcp.prompt()
def create_dashboard_app(app_id: int = 200, app_name: str = "Dashboard") -> str:
    """Workflow to create an analytics dashboard with charts and KPIs."""
    return f"""Create an analytics dashboard APEX application.

Follow these steps:
1. apex_connect()
2. apex_list_tables() — discover available tables
3. apex_create_app(app_id={app_id}, app_name="{app_name}")
4. apex_generate_login(page_id=101)
5. apex_add_page(1, "Dashboard", "blank")
6. For each important table, add metric cards and charts:
   - apex_add_metric_cards(page_id=1, ...) for KPIs
   - apex_add_jet_chart(page_id=1, ...) for visualizations
7. Add CRUD pages for data tables using apex_generate_crud()
8. Add navigation with apex_add_nav_item()
9. apex_finalize_app()"""


@mcp.prompt()
def create_full_app_from_schema() -> str:
    """Workflow to auto-generate a complete app from all tables in the schema."""
    return """Create a complete APEX application from the database schema.

Follow these steps:
1. apex_connect()
2. apex_list_tables() — get all tables
3. apex_detect_relationships(tables) — understand FK relationships
4. apex_create_app(app_id=200, app_name="My Application")
5. apex_generate_login(page_id=101)
6. apex_generate_from_schema(tables=[...], start_page_id=10, include_dashboard=True)
7. apex_finalize_app()
8. apex_validate_app() — check for issues"""


@mcp.prompt()
def inspect_existing_app(app_id: int) -> str:
    """Workflow to thoroughly inspect an existing APEX application."""
    return f"""Inspect the APEX application {app_id} in detail.

Follow these steps:
1. apex_connect()
2. apex_get_app_details({app_id}) — get app overview
3. For each page:
   - apex_get_page_details({app_id}, page_id)
   - apex_list_regions({app_id}, page_id)
   - apex_list_items({app_id}, page_id)
4. apex_list_lovs({app_id}) — shared LOVs
5. apex_list_auth_schemes({app_id}) — authorization
6. apex_validate_app() — check for issues
7. Summarize findings with recommendations"""


@mcp.prompt()
def add_rest_api(table_name: str) -> str:
    """Workflow to expose a table as REST API endpoints via ORDS."""
    return f"""Create REST API endpoints for the table {table_name}.

Follow these steps:
1. apex_connect()
2. apex_describe_table("{table_name}") — understand structure
3. apex_generate_rest_endpoints("{table_name}", base_path="{table_name.lower()}", require_auth=True)
4. The endpoints will be:
   - GET    /ords/schema/{table_name.lower()}/      — list all
   - POST   /ords/schema/{table_name.lower()}/      — create
   - GET    /ords/schema/{table_name.lower()}/:id    — get one
   - PUT    /ords/schema/{table_name.lower()}/:id    — update
   - DELETE /ords/schema/{table_name.lower()}/:id    — delete"""


def main():
    """Entry point — supports stdio, streamable-http, and sse transports."""
    parser = argparse.ArgumentParser(
        prog="apex-mcp",
        description="Oracle APEX MCP Server — 116 tools for APEX development via AI",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Host to bind for HTTP transports (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port to bind for HTTP transports (default: 8000)",
    )
    parser.add_argument(
        "--path",
        default=os.environ.get("MCP_PATH", None),
        help="Endpoint path (streamable-http default: /mcp, sse default: /sse)",
    )

    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        path = args.path or "/mcp"
        mcp.run(transport="streamable-http", host=args.host, port=args.port, path=path)
    elif args.transport == "sse":
        path = args.path or "/sse"
        mcp.run(transport="sse", host=args.host, port=args.port, path=path)


if __name__ == "__main__":
    main()
