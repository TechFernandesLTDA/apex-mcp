# apex-mcp — Oracle APEX MCP Server

> Build, inspect, and modify **Oracle APEX 24.2** applications via natural language using Claude Code.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-green)](https://github.com/jlowin/fastmcp)
[![Oracle APEX](https://img.shields.io/badge/Oracle_APEX-24.2-red)](https://apex.oracle.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

**apex-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes **82 tools** for building Oracle APEX 24.2 applications through AI assistants such as Claude Code. Built on FastMCP 3.x and Python 3.11+, it connects to Oracle Autonomous Database via the `oracledb` thin driver (mTLS wallet — no Oracle Instant Client required). Instead of navigating the APEX App Builder UI, you describe what you want and the AI does the work: create apps, generate CRUD pages, add JET charts, configure auth schemes, export pages, generate REST endpoints, and more — all through natural language.

```
"Create a full HR app from the EMPLOYEES and DEPARTMENTS tables with an analytics dashboard"
→ apex_connect()
→ apex_generate_from_schema(["EMPLOYEES","DEPARTMENTS"], start_page_id=10, include_dashboard=True)
→ apex_add_nav_item("Dashboard", 1, 10, "fa-home")
→ apex_finalize_app()
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install fastmcp oracledb
```

### 2. Clone and install the server

```bash
git clone https://github.com/techfernandes/apex-mcp.git
cd apex-mcp/mcp-server
pip install -e .
```

### 3. Configure `.mcp.json` in your project root

```json
{
  "mcpServers": {
    "apex-dev": {
      "command": "python",
      "args": ["-m", "apex_mcp.server"],
      "cwd": "/path/to/apex-mcp/mcp-server",
      "env": {
        "ORACLE_DB_USER": "MY_SCHEMA",
        "ORACLE_DB_PASS": "MySecurePass@2024",
        "ORACLE_DSN": "mydb_tp",
        "ORACLE_WALLET_DIR": "/path/to/wallet",
        "ORACLE_WALLET_PASSWORD": "wallet_password",
        "APEX_WORKSPACE_ID": "YOUR_WORKSPACE_ID_HERE",
        "APEX_SCHEMA": "MY_SCHEMA",
        "APEX_WORKSPACE_NAME": "MYWORKSPACE"
      }
    }
  }
}
```

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ORACLE_DB_USER` | Yes | Database username (workspace schema) | `MY_SCHEMA` |
| `ORACLE_DB_PASS` | Yes | Database password | `MyPass@2024` |
| `ORACLE_DSN` | Yes | TNS alias from `tnsnames.ora` | `mydb_tp` |
| `ORACLE_WALLET_DIR` | Yes | Path to extracted wallet directory | `/myproject/wallet` |
| `ORACLE_WALLET_PASSWORD` | Yes | Wallet decryption password | `wallet123` |
| `APEX_WORKSPACE_ID` | Yes | Numeric APEX workspace ID | `8822816515098715` |
| `APEX_SCHEMA` | Yes | Schema associated with APEX workspace | `MY_SCHEMA` |
| `APEX_WORKSPACE_NAME` | No | Workspace name (display only) | `MYWORKSPACE` |

> **Finding your Workspace ID:** APEX Admin Console → Manage Workspaces → click workspace → ID shown in the URL or details panel.
>
> **Finding your DSN:** Open `wallet/tnsnames.ora` — the alias names before `=` are your options. Use the `_tp` alias for APEX (OLTP).
>
> **Wallet directory:** Point to the extracted folder containing `tnsnames.ora`, `sqlnet.ora`, `cwallet.sso`, and `ewallet.p12`. Do not point to the ZIP file.

### 4. Verify in Claude Code

```
/mcp
```

You should see `apex-dev` with **82 tools**. If not, call `apex_check_requirements()` to diagnose.

---

## Tool Reference

### Setup & Diagnostics (4)

| Tool | Description |
|------|-------------|
| `apex_setup_guide()` | Full setup guide with all requirements and step-by-step instructions |
| `apex_check_requirements()` | Verify Python packages, env vars, wallet contents, and DB connectivity |
| `apex_check_permissions()` | Audit database grants needed for all MCP operations |
| `apex_fix_permissions()` | Attempt to auto-grant missing privileges (requires ADMIN/DBA connection) |

### Connection (3)

| Tool | Description |
|------|-------------|
| `apex_connect(...)` | Connect to Oracle ADB using env vars or explicit credentials |
| `apex_run_sql(sql, max_rows?)` | Execute any SELECT or PL/SQL statement and return results |
| `apex_status()` | Show current session state: app, pages built, components created |

### App Lifecycle (7)

| Tool | Description |
|------|-------------|
| `apex_list_apps()` | List all applications in the workspace |
| `apex_create_app(app_id, app_name, ...)` | Create app scaffold with Universal Theme 42, auth, and nav menu |
| `apex_finalize_app()` | Commit the import session — must be called when done building |
| `apex_delete_app(app_id)` | Permanently delete an application |
| `apex_export_app(app_id, output_path?)` | Export application as a SQL script |
| `apex_describe_page(app_id, page_id)` | Describe a page's purpose and component summary |
| `apex_dry_run_preview(enabled)` | Toggle dry-run mode: queue PL/SQL without executing, then return the full log |

### Pages (2)

| Tool | Description |
|------|-------------|
| `apex_add_page(page_id, page_name, page_type?, ...)` | Add a page: blank / form / report / login / dashboard / modal |
| `apex_list_pages(app_id?)` | List all pages via the APEX dictionary |

### Components (5)

| Tool | Description |
|------|-------------|
| `apex_add_region(page_id, region_name, region_type?, ...)` | Add a region: static / interactive report / form / chart / PL/SQL |
| `apex_add_item(page_id, region_name, item_name, item_type?, ...)` | Add a form field to a region |
| `apex_add_button(page_id, region_name, button_name, label, action?, ...)` | Add a button with submit, redirect, or custom action |
| `apex_add_process(page_id, process_name, process_type?, ...)` | Add a server-side process: DML / PL/SQL / AJAX on-demand |
| `apex_add_dynamic_action(page_id, da_name, event?, ...)` | Add a Dynamic Action with event, condition, and true/false actions |

### Shared Components (5)

| Tool | Description |
|------|-------------|
| `apex_add_lov(lov_name, lov_type?, sql_query?, static_values?)` | Create a shared List of Values (SQL query or static) |
| `apex_add_auth_scheme(scheme_name, function_body, error_message?, ...)` | Create a PL/SQL-based authorization scheme |
| `apex_add_nav_item(item_name, target_page, sequence?, icon?, ...)` | Add an item to the navigation menu |
| `apex_add_app_item(item_name, scope?, protection?)` | Create a session-level application item (global variable) |
| `apex_add_app_process(process_name, plsql_body, point?, ...)` | Create an application-level process running at a specified page event |

### Schema Introspection (3)

| Tool | Description |
|------|-------------|
| `apex_list_tables(pattern?, include_columns?)` | List all tables in the schema, optionally filtered by name pattern |
| `apex_describe_table(table_name)` | Full table metadata: columns, data types, PKs, FKs, and indexes |
| `apex_detect_relationships(tables)` | Detect FK relationships between a list of tables |

### Generators (3)

| Tool | Description |
|------|-------------|
| `apex_generate_crud(table_name, list_page_id, form_page_id, ...)` | Full CRUD: Interactive Report list + form with DML, auto-inferred item types |
| `apex_generate_dashboard(page_id, kpi_queries?, ir_sql?, ...)` | Dashboard page with KPI cards and an Interactive Report |
| `apex_generate_login(page_id?, app_name?, auth_process_plsql?, ...)` | Professional login page with branded layout |

### User Management (2)

| Tool | Description |
|------|-------------|
| `apex_create_user(username, password, email?, ...)` | Create an APEX workspace user |
| `apex_list_users(workspace_id?)` | List all users in the workspace |

### JavaScript (3)

| Tool | Description |
|------|-------------|
| `apex_add_page_js(page_id, javascript_code, js_file_urls?)` | Add inline JavaScript to a specific page |
| `apex_add_global_js(function_name, javascript_code, ...)` | Generate a reusable JS function with upload instructions for Static Files |
| `apex_generate_ajax_handler(page_id, callback_name, plsql_code, ...)` | Create an AJAX on-demand process + matching JavaScript caller function |

### Inspection & Editing (14)

| Tool | Description |
|------|-------------|
| `apex_get_app_details(app_id)` | Full application metadata from the APEX dictionary |
| `apex_get_page_details(app_id, page_id)` | All components on a page: regions, items, processes, DAs |
| `apex_list_regions(app_id, page_id)` | List regions on a page with type and source |
| `apex_list_items(app_id, page_id, region_name?)` | List form items on a page, optionally filtered by region |
| `apex_list_processes(app_id, page_id)` | List server-side processes on a page |
| `apex_list_dynamic_actions(app_id, page_id)` | List Dynamic Actions on a page |
| `apex_list_lovs(app_id)` | List all shared LOVs in the application |
| `apex_list_auth_schemes(app_id)` | List all authorization schemes |
| `apex_update_region(app_id, page_id, region_name, ...)` | Update region properties (SQL source, title, template, etc.) |
| `apex_update_item(app_id, page_id, item_name, ...)` | Update item properties (LOV, type, label, default, etc.) |
| `apex_delete_page(app_id, page_id)` | Delete a page from an application |
| `apex_delete_region(app_id, page_id, region_name)` | Delete a specific region from a page |
| `apex_copy_page(src_app, src_page, tgt_app, tgt_page, ...)` | Copy a page between applications |
| `apex_diff_app(app_id)` | Compare current app state against session baseline, showing changes |

### Validations (2)

| Tool | Description |
|------|-------------|
| `apex_add_item_validation(page_id, item_name, validation_type, ...)` | Add a server-side validation to a form item |
| `apex_add_item_computation(page_id, item_name, computation_type, ...)` | Add a computation to derive an item's value at page load or submit |

### Visual — Charts & Cards (7)

| Tool | Description |
|------|-------------|
| `apex_add_jet_chart(page_id, region_name, chart_type, sql_query, ...)` | Oracle JET chart: bar / bar_horizontal / line / area / pie / donut / combo |
| `apex_add_gauge(page_id, region_name, sql_query, ...)` | Dial gauge with configurable min, max, and threshold bands |
| `apex_add_funnel(page_id, region_name, sql_query, ...)` | Funnel chart for pipeline or conversion stages |
| `apex_add_sparkline(page_id, region_name, metrics, ...)` | Inline sparkline trend charts embedded in KPI cards |
| `apex_add_metric_cards(page_id, region_name, metrics, style?, columns?)` | Animated metric tiles — styles: gradient / white / dark |
| `apex_add_calendar(page_id, region_name, sql_query, date_column, ...)` | Calendar region for date-based data, month or week view |
| `apex_generate_analytics_page(page_id, page_name, metrics, charts, ...)` | Complete analytics page in one call: metric cards + multiple JET charts |

### Advanced Components (10)

| Tool | Description |
|------|-------------|
| `apex_generate_report_page(page_id, page_name, sql_query, ...)` | Interactive Report page with optional filter bar items |
| `apex_generate_wizard(start_page_id, steps, wizard_title, ...)` | Multi-step wizard with previous/next navigation and finish redirect |
| `apex_add_notification_region(page_id, region_name, message, ...)` | Info / warning / success / error alert region, optionally dismissible |
| `apex_add_page_css(page_id, css_code, ...)` | Inject inline CSS scoped to a specific page |
| `apex_add_interactive_grid(page_id, region_name, table_name, ...)` | Editable Interactive Grid (spreadsheet-style) with optional add-row |
| `apex_bulk_add_items(page_id, region_name, items)` | Create multiple form items in one call from a list of definitions |
| `apex_validate_app()` | Run an app health check and return a score (0-100) plus issues list |
| `apex_preview_page(app_id, page_id)` | Return a structural preview of a page without opening a browser |
| `apex_add_search_bar(page_id, region_name, target_region, ...)` | Add a search input wired to filter an existing Interactive Report |
| `apex_generate_from_schema(tables, start_page_id, ...)` | Generate a complete multi-page app (CRUD + optional dashboard) from a list of tables |

### UX Components (7)

| Tool | Description |
|------|-------------|
| `apex_generate_modal_form(page_id, region_name, table_name, pk_item_name)` | Modal popup form on an existing page without a separate page |
| `apex_add_master_detail(page_id, master_region_name, master_sql, ...)` | Two linked IRs where detail filters on master row selection |
| `apex_add_timeline(page_id, region_name, sql_query, date_col, ...)` | Vertical timeline region for audit trails and history |
| `apex_add_breadcrumb(page_id, entries)` | Add a breadcrumb trail to a page |
| `apex_add_faceted_search(page_id, region_name, sql_query, facets, ...)` | Faceted search sidebar + Interactive Report for multi-dimensional filtering |
| `apex_add_chart_drilldown(page_id, chart_region_name, target_item_name, ...)` | Wire a chart click to filter an Interactive Report on the same page |
| `apex_add_file_upload(page_id, region_name, item_name, table_name, ...)` | File upload item backed by a BLOB column with filename and MIME type |

### DevOps (5)

| Tool | Description |
|------|-------------|
| `apex_generate_rest_endpoints(table_name, base_path, require_auth?, ...)` | Generate ORDS REST endpoints: GET/POST collection + GET/PUT/DELETE single row |
| `apex_export_page(app_id, page_id, output_path?)` | Export a single page as a SQL script |
| `apex_generate_docs(app_id)` | Auto-generate Markdown documentation for an application |
| `apex_begin_batch()` | Start batch mode: queue all subsequent PL/SQL for a single DB round-trip |
| `apex_commit_batch()` | Execute all queued batch operations and return the execution log |

---

## Code Examples

### 1. Full app from schema in one call

```python
apex_connect()
apex_create_app(app_id=200, app_name="Order Management")
apex_generate_login(page_id=101, app_name="Order Management")

# Inspect available tables
apex_list_tables()
apex_detect_relationships(["ORDERS", "CUSTOMERS", "ORDER_ITEMS", "PRODUCTS"])

# Generate the entire app: CRUD pages for each table + a dashboard
apex_generate_from_schema(
    tables=["ORDERS", "CUSTOMERS", "ORDER_ITEMS", "PRODUCTS"],
    start_page_id=10,
    include_dashboard=True
)

# Add navigation
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Orders", 10, 20, "fa-shopping-cart")
apex_add_nav_item("Customers", 20, 30, "fa-users")

apex_finalize_app()
```

### 2. Analytics page with JET charts

```python
apex_generate_analytics_page(
    page_id=5,
    page_name="Analytics",
    metrics=[
        {"label": "Total Orders",  "sql": "SELECT COUNT(*) FROM ORDERS",            "icon": "fa-shopping-cart", "color": "#1E88E5"},
        {"label": "Open Orders",   "sql": "SELECT COUNT(*) FROM ORDERS WHERE STATUS='OPEN'", "icon": "fa-clock",         "color": "#FF9800"},
        {"label": "Total Revenue", "sql": "SELECT SUM(AMOUNT) FROM ORDERS",          "icon": "fa-dollar",        "color": "#43A047"},
    ],
    charts=[
        {
            "region_name": "Orders by Status",
            "chart_type": "pie",
            "sql_query": "SELECT STATUS LABEL, COUNT(*) VALUE FROM ORDERS GROUP BY STATUS",
            "color_palette": ["#1E88E5", "#43A047", "#FF9800", "#E53935"]
        },
        {
            "region_name": "Monthly Revenue",
            "chart_type": "line",
            "sql_query": "SELECT TO_CHAR(ORDER_DATE,'MM/YYYY') LABEL, SUM(AMOUNT) VALUE FROM ORDERS GROUP BY TO_CHAR(ORDER_DATE,'MM/YYYY') ORDER BY 1"
        },
        {
            "region_name": "Top Customers",
            "chart_type": "bar_horizontal",
            "sql_query": "SELECT C.NAME LABEL, COUNT(*) VALUE FROM ORDERS O JOIN CUSTOMERS C ON C.ID=O.CUSTOMER_ID GROUP BY C.NAME ORDER BY 2 DESC FETCH FIRST 10 ROWS ONLY"
        }
    ]
)
```

### 3. ORDS REST API generation

```python
# Generate GET/POST /ords/myschema/orders/ and GET/PUT/DELETE /ords/myschema/orders/:id
apex_generate_rest_endpoints(
    table_name="ORDERS",
    base_path="orders",
    require_auth=True
)

# Add a custom query endpoint for reporting
apex_generate_rest_endpoints(
    table_name="ORDER_ITEMS",
    base_path="order-items",
    require_auth=True
)

# Verify the endpoints were registered
apex_run_sql("SELECT pattern, method FROM user_ords_endpoints WHERE pattern LIKE '/orders%'")
```

### 4. App documentation generation

```python
# Generate full Markdown docs for an existing app
docs = apex_generate_docs(app_id=200)

# The output includes:
#   - App metadata (name, version, theme, auth scheme)
#   - Page inventory with types and descriptions
#   - Component breakdown per page (regions, items, processes, DAs)
#   - Shared components: LOVs, auth schemes, app items
#   - Navigation structure
#   - Known issues from apex_validate_app()

# You can pipe the output to a file or include it in a wiki
```

---

## Architecture

```
mcp-server/
├── pyproject.toml
└── apex_mcp/
    ├── server.py           # FastMCP 3.x entry point — 82 tools registered
    ├── config.py           # Environment variable loading and defaults
    ├── db.py               # ConnectionManager singleton (mTLS, auto-reconnect)
    ├── ids.py              # Session-scoped unique ID generator (time-salted)
    ├── templates.py        # Universal Theme 42 template ID constants
    ├── session.py          # Import session state: tracks components for cross-referencing
    └── tools/
        ├── sql_tools.py        # apex_connect, apex_run_sql, apex_status
        ├── app_tools.py        # apex_create_app, apex_delete_app, apex_export_app, ...
        ├── page_tools.py       # apex_add_page, apex_list_pages
        ├── component_tools.py  # apex_add_region, apex_add_item, apex_add_button, ...
        ├── shared_tools.py     # apex_add_lov, apex_add_auth_scheme, apex_add_nav_item, ...
        ├── schema_tools.py     # apex_list_tables, apex_describe_table, apex_detect_relationships
        ├── generator_tools.py  # apex_generate_crud, apex_generate_dashboard, apex_generate_login
        ├── js_tools.py         # apex_add_page_js, apex_add_global_js, apex_generate_ajax_handler
        ├── inspect_tools.py    # apex_get_page_details, apex_update_region, apex_diff_app, ...
        ├── user_tools.py       # apex_create_user, apex_list_users
        ├── setup_tools.py      # apex_setup_guide, apex_check_requirements, ...
        ├── validation_tools.py # apex_add_item_validation, apex_add_item_computation
        ├── visual_tools.py     # apex_add_jet_chart, apex_add_gauge, apex_add_metric_cards, ...
        ├── advanced_tools.py   # apex_generate_from_schema, apex_generate_wizard, ...
        └── devops_tools.py     # apex_generate_rest_endpoints, apex_export_page, apex_begin_batch, ...
```

**Key design points:**

- **FastMCP 3.x** — tools registered via `mcp.tool()` decorator, served over stdio for MCP clients
- **Oracle oracledb thin mode** — mTLS wallet connection; Oracle Instant Client is not required
- **Session state singleton** — `session.py` tracks created component IDs so later tools can reference regions by name without re-querying the DB
- **Dry-run mode** — `apex_dry_run_preview(enabled=True)` queues all PL/SQL without executing; returns the full script for review
- **Batch mode** — `apex_begin_batch()` / `apex_commit_batch()` coalesces multiple operations into a single DB round-trip
- **Column cache** — table column metadata is cached per session to avoid repeated dictionary queries during CRUD generation
- **ID generator** — time-salted sequential IDs prevent conflicts with existing APEX component IDs

---

## Requirements

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ (3.14 tested) |
| fastmcp | 3.x |
| oracledb | 2.x or 3.x (thin mode) |
| Oracle Instant Client | **Not required** (thin mode) |
| Oracle APEX | 24.x (24.2 recommended) |
| Oracle Database | Autonomous Database 23ai or compatible |

The database schema must be the schema associated with your APEX workspace. Most required privileges are granted automatically to workspace-linked schemas. Use `apex_check_permissions()` to verify, and `apex_fix_permissions()` to resolve any gaps.

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `DPI-1047: Cannot locate a 64-bit Oracle Client` | Outdated oracledb | `pip install --upgrade oracledb` |
| `ORA-28759: failure to open file` | Wallet path points to ZIP | Set `ORACLE_WALLET_DIR` to the **extracted** folder |
| `ORA-01017: invalid username/password` | Wrong credentials | Check `ORACLE_DB_USER` and `ORACLE_DB_PASS` |
| `TNS-03505: Failed to resolve name` | Wrong DSN alias | Open `wallet/tnsnames.ora` and copy an alias exactly |
| `ORA-20987: Application does not exist` | Wrong workspace ID | Verify `APEX_WORKSPACE_ID` in APEX Admin |
| `ORA-01031: insufficient privileges` | Missing grants | Run the grant script shown by `apex_check_permissions()` |
| `No module named 'apex_mcp'` | Wrong `cwd` in `.mcp.json` | Set `cwd` to the `mcp-server/` directory |
| `apex_finalize_app: no active session` | Forgot `apex_create_app` | Call `apex_create_app()` before adding any component |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-tool`
3. Add your tool in `apex_mcp/tools/`
4. Register it in `apex_mcp/server.py`
5. Include a docstring describing parameters and APEX best practices
6. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE)

---

Built for Oracle APEX 24.2 + Universal Theme 42. Tested with Oracle Autonomous Database 23ai.
