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
    instructions="""You are connected to an Oracle APEX 24.2 development environment via MCP.

## Lifecycle
1. `apex_connect()` → 2. `apex_create_app(app_id, app_name)` → 3. add pages/regions/items → 4. `apex_finalize_app()`
Always finalize. For existing apps: `apex_list_apps()` → `apex_get_app_details(id)` → inspect/update.

## Quick Build Pattern
```
apex_connect()
apex_create_app(app_id=200, app_name="My App")
apex_generate_login(page_id=101)
apex_add_page(1, "Dashboard", "blank")
apex_generate_dashboard(page_id=1)
apex_generate_crud("MY_TABLE", 10, 11)
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Records", 10, 20, "fa-table")
apex_finalize_app()
```

## High-Level Generators (prefer these for speed)
- `apex_generate_from_schema(tables=[...])` — full app from multiple tables with dashboard + CRUD + nav
- `apex_generate_crud(table, list_page, form_page)` — IR list + form for one table
- `apex_generate_analytics_page(page_id, metrics=[...], charts=[...])` — metrics + charts in one call
- `apex_generate_report_page(page_id, sql_query, filter_items=[...])` — IR + filter items
- `apex_generate_wizard(start_page_id, steps=[...])` — multi-step wizard
- `apex_generate_modal_form(page_id, region_name, table_name, pk_item_name)` — inline modal dialog

## Conventions
- Items: `P{page_id}_{COLUMN}` (auto-prefixed) | AJAX callbacks: UPPERCASE | Nav sequences: multiples of 10
- Auth schemes: IS_ prefix | Date format: DD/MM/YYYY | SQL must alias LABEL + VALUE for charts
- Batch mode: `apex_begin_batch()` → multiple adds → `apex_commit_batch()` (1 DB round-trip)
- Dry-run: `apex_dry_run_preview(enabled=True)` logs PL/SQL without executing

## After Creating
Access at: f?p={app_id} (relative to APEX base URL)
""",
)

# ── Tool annotations ─────────────────────────────────────────────────────────
_READ = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_READ_OPEN = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}
_SAFE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}
_WRITE = {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False}
_DELETE = {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False}

# ── Register all tools with concise descriptions for AI clients ──────────────
# description= overrides the (verbose) Python docstring in the MCP tool listing.
# This saves ~50K tokens of context window for LLMs like Claude Opus 4.6.

# Setup & diagnostics
mcp.tool(description="Show setup requirements and instructions for this APEX MCP server.", annotations=_READ, tags={"setup"})(apex_setup_guide)
mcp.tool(description="Verify Oracle connection, APEX workspace, and grants are configured.", annotations=_READ, tags={"setup"})(apex_check_requirements)
mcp.tool(description="Check Oracle grants and APEX object access permissions.", annotations=_READ, tags={"setup"})(apex_check_permissions)
mcp.tool(description="Auto-fix common Oracle permission issues (grants, synonyms).", annotations=_SAFE, tags={"setup"})(apex_fix_permissions)
mcp.tool(description="Refresh Universal Theme 42 template IDs from the live database.", annotations=_SAFE, tags={"setup"})(apex_refresh_templates)
mcp.tool(description="Run APEX health check: score 0-100 with issues list.", annotations=_READ, tags={"setup"})(apex_health_check)
mcp.tool(description="Get audit log of recent MCP operations in this session.", annotations=_READ, tags={"setup"})(apex_get_audit_log)

# Connection & session
mcp.tool(description="Connect to Oracle ADB via mTLS wallet. Must be called first.", annotations=_SAFE, tags={"connection"})(apex_connect)
mcp.tool(description="Execute any SQL statement (SELECT/DML/DDL). Returns rows or affected count.", annotations=_READ_OPEN, tags={"connection"})(apex_run_sql)
mcp.tool(description="Show current connection status, session state, and active app.", annotations=_READ, tags={"connection"})(apex_status)

# App lifecycle
mcp.tool(description="List all APEX applications in the workspace.", annotations=_READ, tags={"app"})(apex_list_apps)
mcp.tool(description="Create a new APEX app and start an import session. Call apex_finalize_app() when done.", annotations=_WRITE, tags={"app"})(apex_create_app)
mcp.tool(description="Finalize and commit the app. Must be called after all pages/components are added.", annotations=_WRITE, tags={"app"})(apex_finalize_app)
mcp.tool(description="Delete an APEX application permanently.", annotations=_DELETE, tags={"app"})(apex_delete_app)
mcp.tool(description="Export an app as SQL install script.", annotations=_READ, tags={"app"})(apex_export_app)
mcp.tool(description="Describe a page's components in human-readable text.", annotations=_READ, tags={"app"})(apex_describe_page)
mcp.tool(description="Toggle dry-run mode: log PL/SQL without executing. Returns log when disabled.", annotations=_SAFE, tags={"app"})(apex_dry_run_preview)
mcp.tool(description="Undo the last created component (region, item, button, etc.).", annotations=_DELETE, tags={"app"})(apex_undo_last)

# Pages
mcp.tool(description="Add a new page to the app. page_mode: Normal or Modal Dialog.", annotations=_WRITE, tags={"page"})(apex_add_page)
mcp.tool(description="List all pages in the current session or an existing app.", annotations=_READ, tags={"page"})(apex_list_pages)

# Components
mcp.tool(description="Add a region to a page. Types: STATIC, IR (Interactive Report), PLSQL, chart, blank.", annotations=_WRITE, tags={"component"})(apex_add_region)
mcp.tool(description="Add a form item. Types: text, number, date, select, textarea, hidden, yes_no, display_only. Auto-prefixed P{page_id}_.", annotations=_WRITE, tags={"component"})(apex_add_item)
mcp.tool(description="Add a button to a region (CREATE, SAVE, DELETE, CANCEL, or custom).", annotations=_WRITE, tags={"component"})(apex_add_button)
mcp.tool(description="Add a page process: PL/SQL block, DML on table, or branch redirect.", annotations=_WRITE, tags={"component"})(apex_add_process)
mcp.tool(description="Add a dynamic action (client-side event handler). Actions: execute_javascript, set_value, refresh, show, hide, submit.", annotations=_WRITE, tags={"component"})(apex_add_dynamic_action)

# Shared components
mcp.tool(description="Create a List of Values (LOV) — static or SQL-based — for select items.", annotations=_WRITE, tags={"shared"})(apex_add_lov)
mcp.tool(description="Create an authorization scheme (IS_ADMIN, IS_MANAGER, etc.).", annotations=_WRITE, tags={"shared"})(apex_add_auth_scheme)
mcp.tool(description="Add a navigation menu item linking to a page.", annotations=_WRITE, tags={"shared"})(apex_add_nav_item)
mcp.tool(description="Create an application-level item (global variable available on all pages).", annotations=_WRITE, tags={"shared"})(apex_add_app_item)
mcp.tool(description="Create an application-level process (runs on every page load or session init).", annotations=_WRITE, tags={"shared"})(apex_add_app_process)

# Schema introspection
mcp.tool(description="List all tables/views in the current Oracle schema with row counts.", annotations=_READ, tags={"schema"})(apex_list_tables)
mcp.tool(description="Describe table columns, types, PKs, and FKs. Cached per session.", annotations=_READ, tags={"schema"})(apex_describe_table)
mcp.tool(description="Auto-detect FK relationships between a list of tables.", annotations=_READ, tags={"schema"})(apex_detect_relationships)

# Generators (high-level)
mcp.tool(description="Generate full CRUD: IR list page + form page with DML processes for a table.", annotations=_WRITE, tags={"generator"})(apex_generate_crud)
mcp.tool(description="Generate a dashboard page with KPI metric cards and JET charts.", annotations=_WRITE, tags={"generator"})(apex_generate_dashboard)
mcp.tool(description="Generate a login page (page 101) with APEX authentication.", annotations=_WRITE, tags={"generator"})(apex_generate_login)

# User management
mcp.tool(description="Create an APEX workspace user with role (ADMIN/DEVELOPER/END_USER).", annotations=_WRITE, tags={"user"})(apex_create_user)
mcp.tool(description="List all users in the APEX workspace.", annotations=_READ, tags={"user"})(apex_list_users)

# JavaScript
mcp.tool(description="Add inline JavaScript to a specific page.", annotations=_WRITE, tags={"javascript"})(apex_add_page_js)
mcp.tool(description="Add global JavaScript to all pages via Page 0.", annotations=_WRITE, tags={"javascript"})(apex_add_global_js)
mcp.tool(description="Create an AJAX callback process (PL/SQL) callable from client-side JS.", annotations=_WRITE, tags={"javascript"})(apex_generate_ajax_handler)

# Inspection & editing of existing apps
mcp.tool(description="Get full metadata for an existing APEX app (pages, auth, theme).", annotations=_READ, tags={"inspect"})(apex_get_app_details)
mcp.tool(description="Get all components on a page (regions, items, buttons, processes).", annotations=_READ, tags={"inspect"})(apex_get_page_details)
mcp.tool(description="List regions on a page of an existing app.", annotations=_READ, tags={"inspect"})(apex_list_regions)
mcp.tool(description="List items on a page of an existing app.", annotations=_READ, tags={"inspect"})(apex_list_items)
mcp.tool(description="List page processes of an existing app.", annotations=_READ, tags={"inspect"})(apex_list_processes)
mcp.tool(description="List dynamic actions on a page of an existing app.", annotations=_READ, tags={"inspect"})(apex_list_dynamic_actions)
mcp.tool(description="List all LOVs (Lists of Values) in an existing app.", annotations=_READ, tags={"inspect"})(apex_list_lovs)
mcp.tool(description="List authorization schemes in an existing app.", annotations=_READ, tags={"inspect"})(apex_list_auth_schemes)
mcp.tool(description="Update a region's SQL source, title, or template in an existing app.", annotations=_WRITE, tags={"inspect"})(apex_update_region)
mcp.tool(description="Update an item's LOV, label, type, or default in an existing app.", annotations=_WRITE, tags={"inspect"})(apex_update_item)
mcp.tool(description="Delete a page from an existing app.", annotations=_DELETE, tags={"inspect"})(apex_delete_page)
mcp.tool(description="Delete a region from an existing app.", annotations=_DELETE, tags={"inspect"})(apex_delete_region)
mcp.tool(description="Delete an item from an existing app.", annotations=_DELETE, tags={"inspect"})(apex_delete_item)
mcp.tool(description="Delete a button from an existing app.", annotations=_DELETE, tags={"inspect"})(apex_delete_button)
mcp.tool(description="Update page properties (title, mode, auth) in an existing app.", annotations=_WRITE, tags={"inspect"})(apex_update_page)
mcp.tool(description="Copy a page to a new page ID within the same app.", annotations=_WRITE, tags={"inspect"})(apex_copy_page)
mcp.tool(description="Compare app structure before/after changes (diff of pages, regions, items).", annotations=_READ, tags={"inspect"})(apex_diff_app)

# Validations & computations
mcp.tool(description="Add server-side validation to a page item (NOT_NULL, REGEX, SQL, PL/SQL).", annotations=_WRITE, tags={"validation"})(apex_add_item_validation)
mcp.tool(description="Add a computation to set an item's value (STATIC, SQL, PL/SQL, ITEM).", annotations=_WRITE, tags={"validation"})(apex_add_item_computation)

# Visual tools
mcp.tool(description="Add an Oracle JET chart region. Types: bar, line, pie, donut, area. SQL must alias LABEL + VALUE.", annotations=_WRITE, tags={"visual"})(apex_add_jet_chart)
mcp.tool(description="Add a gauge/dial chart with min/max/thresholds. SQL must return a VALUE column.", annotations=_WRITE, tags={"visual"})(apex_add_gauge)
mcp.tool(description="Add a funnel chart. SQL must alias LABEL + VALUE ordered by sequence.", annotations=_WRITE, tags={"visual"})(apex_add_funnel)
mcp.tool(description="Add sparkline mini-charts with trend lines. Provide metrics list with sql + trend_sql.", annotations=_WRITE, tags={"visual"})(apex_add_sparkline)
mcp.tool(description="Add styled KPI metric cards (gradient/flat/outline). Each metric: label + sql + icon + color.", annotations=_WRITE, tags={"visual"})(apex_add_metric_cards)
mcp.tool(description="Add a calendar region. SQL must include a date column and a title column.", annotations=_WRITE, tags={"visual"})(apex_add_calendar)
mcp.tool(description="Generate a full analytics page with metric cards + multiple JET charts in one call.", annotations=_WRITE, tags={"visual"})(apex_generate_analytics_page)

# Advanced generators & utilities
mcp.tool(description="Generate an IR report page with optional filter items (text/select/date).", annotations=_WRITE, tags={"generator"})(apex_generate_report_page)
mcp.tool(description="Generate a multi-step wizard (2-6 steps) with progress bar, items, and navigation buttons.", annotations=_WRITE, tags={"generator"})(apex_generate_wizard)
mcp.tool(description="Add an inline notification/alert (info/success/warning/error) with optional dismiss.", annotations=_WRITE, tags={"advanced"})(apex_add_notification_region)
mcp.tool(description="Add inline CSS to a specific page via a hidden PL/SQL region.", annotations=_WRITE, tags={"advanced"})(apex_add_page_css)
mcp.tool(description="Add global CSS to ALL pages via Page 0. Use for branding and theme overrides.", annotations=_WRITE, tags={"advanced"})(apex_add_global_css)
mcp.tool(description="Add an Interactive Grid (editable spreadsheet). Supports inline editing + add row.", annotations=_WRITE, tags={"advanced"})(apex_add_interactive_grid)
mcp.tool(description="Add multiple form items in one call. Each: {name, type, label, lov, required, default}.", annotations=_WRITE, tags={"advanced"})(apex_bulk_add_items)
mcp.tool(description="Validate an APEX app: check SQL, page refs, missing items. Returns score 0-100 + issues.", annotations=_READ, tags={"validation"})(apex_validate_app)
mcp.tool(description="Get the preview URL for a page (f?p=APP:PAGE).", annotations=_READ, tags={"advanced"})(apex_preview_page)
mcp.tool(description="Add a search bar that filters an IR region on keystroke via Dynamic Action.", annotations=_WRITE, tags={"advanced"})(apex_add_search_bar)
mcp.tool(description="Generate a complete app from a list of tables: CRUD pages + dashboard + navigation.", annotations=_WRITE, tags={"generator"})(apex_generate_from_schema)

# Component tools — modal, master-detail, timeline, breadcrumb, faceted search, drilldown, file upload
mcp.tool(description="Create an inline modal popup form (no separate page). Returns region_static_id for JS open.", annotations=_WRITE, tags={"generator"})(apex_generate_modal_form)
mcp.tool(description="Create master IR + detail IR on same page. Row click in master refreshes detail.", annotations=_WRITE, tags={"advanced"})(apex_add_master_detail)
mcp.tool(description="Add a vertical timeline region. SQL must return date_col, title_col, body_col.", annotations=_WRITE, tags={"advanced"})(apex_add_timeline)
mcp.tool(description="Add breadcrumb navigation with ordered entries [{label, page_id}].", annotations=_WRITE, tags={"advanced"})(apex_add_breadcrumb)
mcp.tool(description="Add faceted search: filter SELECT_LISTs + IR. Facets: [{column, label, type}].", annotations=_WRITE, tags={"advanced"})(apex_add_faceted_search)
mcp.tool(description="Add chart drilldown: click chart series → set hidden item → refresh IR.", annotations=_WRITE, tags={"advanced"})(apex_add_chart_drilldown)
mcp.tool(description="Add a FILE_BROWSE item + after-submit process to store uploads as BLOB.", annotations=_WRITE, tags={"advanced"})(apex_add_file_upload)

# DevOps
mcp.tool(description="Generate ORDS REST endpoints (GET/POST/PUT/DELETE) for a table.", annotations=_WRITE, tags={"devops"})(apex_generate_rest_endpoints)
mcp.tool(description="Export a single page as SQL install script.", annotations=_READ, tags={"devops"})(apex_export_page)
mcp.tool(description="Auto-generate Markdown documentation for an app (pages, regions, items).", annotations=_READ, tags={"devops"})(apex_generate_docs)
mcp.tool(description="Start batch mode: queue PL/SQL operations for a single DB round-trip.", annotations=_SAFE, tags={"devops"})(apex_begin_batch)
mcp.tool(description="Execute all queued batch operations. rollback_on_error=True (default) rolls back on failure.", annotations=_WRITE, tags={"devops"})(apex_commit_batch)

# UI Tools — 20 rich HTML components (rendered via PL/SQL region source)
mcp.tool(description="Add a hero banner with title, subtitle, CTA button, and gradient background.", annotations=_WRITE, tags={"ui"})(apex_add_hero_banner)
mcp.tool(description="Add a horizontal row of KPI cards. Each: {label, sql, icon, color}.", annotations=_WRITE, tags={"ui"})(apex_add_kpi_row)
mcp.tool(description="Add a step progress tracker (horizontal steps with active state).", annotations=_WRITE, tags={"ui"})(apex_add_progress_tracker)
mcp.tool(description="Add a styled alert box (info/success/warning/error) with title and message.", annotations=_WRITE, tags={"ui"})(apex_add_alert_box)
mcp.tool(description="Add a stat card with current value, delta, and trend arrow (up/down).", annotations=_WRITE, tags={"ui"})(apex_add_stat_delta)
mcp.tool(description="Add a grid of quick-link cards. Each: {label, page_id, icon, color}.", annotations=_WRITE, tags={"ui"})(apex_add_quick_links)
mcp.tool(description="Add a ranked leaderboard table. SQL must alias RANK, NAME, VALUE.", annotations=_WRITE, tags={"ui"})(apex_add_leaderboard)
mcp.tool(description="Add a tag/word cloud from SQL (TAG + WEIGHT columns).", annotations=_WRITE, tags={"ui"})(apex_add_tag_cloud)
mcp.tool(description="Add horizontal percent bars. Each: {label, value, max, color}.", annotations=_WRITE, tags={"ui"})(apex_add_percent_bars)
mcp.tool(description="Add an icon list with labels. Each: {icon, label, description, page_id}.", annotations=_WRITE, tags={"ui"})(apex_add_icon_list)
mcp.tool(description="Add a traffic light indicator (red/yellow/green) based on SQL value.", annotations=_WRITE, tags={"ui"})(apex_add_traffic_light)
mcp.tool(description="Add a large spotlight metric with value, label, and optional trend.", annotations=_WRITE, tags={"ui"})(apex_add_spotlight_metric)
mcp.tool(description="Add a side-by-side comparison panel (two columns of metrics).", annotations=_WRITE, tags={"ui"})(apex_add_comparison_panel)
mcp.tool(description="Add an activity/audit stream. SQL must alias TIMESTAMP, USER_NAME, ACTION.", annotations=_WRITE, tags={"ui"})(apex_add_activity_stream)
mcp.tool(description="Add a status matrix grid (rows × columns with colored status cells).", annotations=_WRITE, tags={"ui"})(apex_add_status_matrix)
mcp.tool(description="Add a collapsible/expandable region with toggle.", annotations=_WRITE, tags={"ui"})(apex_add_collapsible_region)
mcp.tool(description="Add a tabs container with multiple content panels.", annotations=_WRITE, tags={"ui"})(apex_add_tabs_container)
mcp.tool(description="Add a responsive grid of data cards. Each: {title, body, icon, badge}.", annotations=_WRITE, tags={"ui"})(apex_add_data_card_grid)
mcp.tool(description="Add a heatmap grid with color intensity based on values.", annotations=_WRITE, tags={"ui"})(apex_add_heatmap_grid)
mcp.tool(description="Add a horizontal ribbon of stat cards with icons and colors.", annotations=_WRITE, tags={"ui"})(apex_add_ribbon_stats)

# Chart Tools — 10 advanced chart types (all SQL must alias LABEL + VALUE)
mcp.tool(description="Add a stacked bar/column chart. SQL: LABEL, VALUE, SERIES.", annotations=_WRITE, tags={"chart"})(apex_add_stacked_chart)
mcp.tool(description="Add a combo chart (bar + line on same axes). SQL: LABEL, BAR_VALUE, LINE_VALUE.", annotations=_WRITE, tags={"chart"})(apex_add_combo_chart)
mcp.tool(description="Add a Pareto chart (bars + cumulative % line). SQL: LABEL, VALUE.", annotations=_WRITE, tags={"chart"})(apex_add_pareto_chart)
mcp.tool(description="Add a scatter plot. SQL: X_VALUE, Y_VALUE, optional LABEL.", annotations=_WRITE, tags={"chart"})(apex_add_scatter_plot)
mcp.tool(description="Add a range chart (min-max bars). SQL: LABEL, LOW_VALUE, HIGH_VALUE.", annotations=_WRITE, tags={"chart"})(apex_add_range_chart)
mcp.tool(description="Add a filled area chart. SQL: LABEL, VALUE.", annotations=_WRITE, tags={"chart"})(apex_add_area_chart)
mcp.tool(description="Add an animated counting number with label (counts up on page load).", annotations=_WRITE, tags={"chart"})(apex_add_animated_counter)
mcp.tool(description="Add a gradient donut chart with center label. SQL: LABEL, VALUE.", annotations=_WRITE, tags={"chart"})(apex_add_gradient_donut)
mcp.tool(description="Add a row of mini sparkline charts. Each: {label, sql, color}.", annotations=_WRITE, tags={"chart"})(apex_add_mini_charts_row)
mcp.tool(description="Add a bubble chart. SQL: X_VALUE, Y_VALUE, BUBBLE_SIZE, optional LABEL.", annotations=_WRITE, tags={"chart"})(apex_add_bubble_chart)

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
