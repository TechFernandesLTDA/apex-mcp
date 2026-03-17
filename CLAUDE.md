# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

apex-mcp is an MCP (Model Context Protocol) server for Oracle APEX 24.2 that exposes 116+ tools to AI clients (Claude, GPT, Gemini, Cursor, VS Code). It generates APEX applications programmatically via PL/SQL using the `wwv_flow_imp_page.*` internal API (same as APEX's own import/export).

## Build & Run

```bash
# Install
pip install -e ".[dev]"

# Run (stdio — default for local AI clients)
python -m apex_mcp
apex-mcp                    # equivalent, via entry point

# Run with HTTP transport
python -m apex_mcp --transport streamable-http --port 8000
python -m apex_mcp --transport sse --port 9000
```

## Testing

```bash
# Unit tests only (no Oracle DB required)
pytest tests/ -v -m "not integration"

# All tests (requires live Oracle ADB + env vars)
pytest tests/ -v

# Single test file
pytest tests/test_session.py -v

# Single test
pytest tests/test_ids.py::test_unique_ids -v
```

Tests require `ORACLE_DB_USER`, `ORACLE_DB_PASS`, `ORACLE_DSN`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD`, `APEX_WORKSPACE_ID`, `APEX_SCHEMA`, `APEX_WORKSPACE_NAME` env vars for integration tests.

## Architecture

### Core Singletons (module-level instances)

- **`db`** (`apex_mcp/db.py`) -- `ConnectionManager` singleton. Thread-safe Oracle connection via oracledb thin driver + mTLS wallet. Has auto-reconnect on transient ORA errors (03113, 03114, 12170, 25408), dry-run mode (logs PL/SQL without executing), and batch mode (queues PL/SQL, executes in one commit). Also provides `safe_col()` / `column_exists()` for APEX version-safe column access with caching.
- **`session`** (`apex_mcp/session.py`) -- `ImportSession` singleton. Tracks all components (pages, regions, items, buttons, LOVs, auth schemes, charts, processes, branches, dynamic actions) created during the `apex_create_app()` to `apex_finalize_app()` lifecycle. Tools use it to resolve cross-references like region IDs. Thread-safe via `threading.RLock`.
- **`ids`** (`apex_mcp/ids.py`) -- `IdGenerator` singleton. Produces unique IDs (base 8,900,000,000,000,000 + random salt + counter) with a named registry to avoid collisions within a session. Reset on each `apex_create_app()` call.

### Supporting Modules

- **`config.py`** -- Reads all env vars at import time; emits `RuntimeWarning` for missing vars (does not crash, so unit tests work without Oracle).
- **`templates.py`** -- Hardcoded Universal Theme 42 template IDs (page, region, button, label, list, report templates) with `discover_template_ids()` to refresh from the live database.
- **`themes.py`** -- Complete Unimed-branded CSS theme (palette `#00995D`) for Universal Theme 42 / Redwood Light.
- **`validators.py`** -- Input validation for page_id, app_id, region_name, sql_query, chart_type, item_type, table_name, color_hex, sequence. All raise `ValueError` with descriptive messages.
- **`guards.py`** -- Pre-condition checks (`require_connection`, `require_session`, `require_page`) returning JSON error strings or `None`.
- **`exceptions.py`** -- Domain exceptions: `ApexMCPError`, `NotConnectedError`, `NoSessionError`, `PageNotFoundError`, `RegionNotFoundError`.
- **`utils.py`** -- `_esc()` (PL/SQL quote escaping), `_blk()` (anonymous block wrapper), `_json()` (JSON serialization with `ensure_ascii=False`), `_sql_to_varchar2()` (converts multi-line SQL to `wwv_flow_string.join(...)` expressions).

### App Creation Lifecycle

Every app build follows: `apex_connect()` -> `apex_create_app()` -> [add pages/regions/items/etc.] -> `apex_finalize_app()`. The session singleton tracks state between these calls. `finalize` closes the import and commits.

### Tool Modules (`apex_mcp/tools/`)

19 modules, each containing related MCP tool functions. All tools are plain async/sync functions registered in `server.py` via `mcp.tool()`. They share access to `db` and `session` singletons.

### PL/SQL Generation Pattern

All tools that create APEX components follow the same pattern:
1. Generate a unique ID via `ids`
2. Build PL/SQL calling `wwv_flow_imp_page.*` or `wwv_flow_imp_shared.*` procedures
3. Execute via `db.plsql()` (respects dry-run/batch modes)
4. Register the component in `session` for cross-reference tracking

### Server Registration (`apex_mcp/server.py`)

The FastMCP server imports all tool functions and registers them with `mcp.tool()`. The `instructions` string in the server definition serves as the system prompt sent to AI clients.

## MCP Configuration (`.mcp.json`)

The project root contains `.mcp.json` for IDE integration (Cursor, VS Code, etc.):

```json
{
  "mcpServers": {
    "apex-mcp": {
      "command": "python",
      "args": ["-m", "apex_mcp"],
      "cwd": "${workspaceFolder}",
      "env": {
        "ORACLE_DB_USER": "YOUR_SCHEMA",
        "ORACLE_DB_PASS": "YOUR_PASSWORD",
        "ORACLE_DSN": "YOUR_DSN",
        "ORACLE_WALLET_DIR": "/path/to/wallet",
        "ORACLE_WALLET_PASSWORD": "YOUR_WALLET_PW",
        "APEX_WORKSPACE_ID": "YOUR_WORKSPACE_ID",
        "APEX_SCHEMA": "YOUR_SCHEMA",
        "APEX_WORKSPACE_NAME": "YOUR_WORKSPACE"
      }
    },
    "sqlcl": {
      "command": "/path/to/sqlcl/bin/sql",
      "args": ["-mcp"],
      "env": {}
    }
  }
}
```

The `sqlcl` entry is the companion SQLcl MCP server -- Oracle's SQL Command Line tool run with `-mcp` flag provides complementary database operations (DDL, data loading, SODA, etc.) alongside apex-mcp's APEX-specific tools.

## Tool Annotations

All tools are registered with MCP tool annotations that describe their behavior to AI clients:

| Annotation | Meaning |
|---|---|
| `_READ` | `readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False` |
| `_READ_OPEN` | Same as `_READ` but `openWorldHint=True` (e.g., `apex_run_sql` -- results depend on DB state) |
| `_SAFE` | `readOnlyHint=False, destructiveHint=False, idempotentHint=True` (side effects but safe to retry) |
| `_WRITE` | `readOnlyHint=False, destructiveHint=False, idempotentHint=False` (creates/modifies resources) |
| `_DELETE` | `readOnlyHint=False, destructiveHint=True, idempotentHint=False` (destructive operations) |

These annotations help AI clients decide when to auto-approve tool calls vs. ask for user confirmation.

## Tool Categories (Tags)

Every tool is registered with a tag. The full tag set:

| Tag | Module(s) | Description |
|---|---|---|
| `setup` | `setup_tools.py` | Setup guide, requirements check, permission check/fix |
| `connection` | `sql_tools.py` | Connect, run SQL, status |
| `app` | `app_tools.py` | Create/finalize/delete/export apps, dry-run |
| `page` | `page_tools.py` | Add/list pages |
| `component` | `component_tools.py` | Add region, item, button, process, dynamic action |
| `shared` | `shared_tools.py` | LOVs, auth schemes, nav items, app items, app processes |
| `schema` | `schema_tools.py` | List/describe tables, detect FK relationships |
| `generator` | `generator_tools.py`, `advanced_tools.py` | High-level generators: CRUD, dashboard, login, report, wizard, modal form, schema-to-app |
| `user` | `user_tools.py` | Create/list APEX users |
| `javascript` | `js_tools.py` | Page JS, global JS, AJAX handlers |
| `inspect` | `inspect_tools.py` | Read/update/delete existing app components, diff |
| `validation` | `validation_tools.py`, `advanced_tools.py` | Item validations, computations, app health check |
| `visual` | `visual_tools.py` | JET charts, gauges, funnels, sparklines, metric cards, calendars, analytics pages |
| `devops` | `devops_tools.py` | REST endpoints, page export, docs generation, batch mode |
| `advanced` | `advanced_tools.py` | Interactive grids, master-detail, timelines, faceted search, chart drilldown, file upload, CSS, notifications, breadcrumbs, search bar, preview |
| `ui` | `ui_tools.py` | 20 rich HTML components: hero banners, KPI rows, progress trackers, alert boxes, stat deltas, quick links, leaderboards, tag clouds, percent bars, icon lists, traffic lights, spotlight metrics, comparison panels, activity streams, status matrices, collapsible regions, tabs containers, data card grids, heatmap grids, ribbon stats |
| `chart` | `chart_tools.py` | 10 advanced chart types: stacked, combo, pareto, scatter, range, area, animated counter, gradient donut, mini charts row, bubble |

## MCP Resources

The server exposes read-only data via MCP resources (`@mcp.resource()`):

| URI | Description |
|-----|-------------|
| `apex://config` | Current configuration and connection status |
| `apex://session` | Active import session state (app, pages, components) |
| `apex://schema/tables` | All tables in current schema (requires connection) |
| `apex://schema/tables/{table_name}` | Column metadata, PKs, FKs for a specific table |
| `apex://apps` | APEX applications in current workspace |
| `apex://apps/{app_id}` | Detailed metadata + page list for a specific app |

Resources are read-only and do not modify state. They complement the tools by providing data without execution overhead.

## MCP Prompts

The server provides workflow templates via MCP prompts (`@mcp.prompt()`):

| Prompt | Parameters | Description |
|--------|-----------|-------------|
| `create_crud_app` | `table_name`, `app_id`, `app_name` | Full CRUD app for a table |
| `create_dashboard_app` | `app_id`, `app_name` | Analytics dashboard with charts and KPIs |
| `create_full_app_from_schema` | (none) | Auto-generate app from all schema tables |
| `inspect_existing_app` | `app_id` | Thorough inspection of an existing app |
| `add_rest_api` | `table_name` | Expose table as ORDS REST endpoints |

Prompts return step-by-step instructions that guide the LLM through multi-tool workflows.

## APEX 24.2 Specific Considerations

### JSON_ATTRIBUTES vs attribute_01..25

APEX 24.2 began transitioning some component metadata from the legacy `attribute_01` through `attribute_25` positional columns to a structured `JSON_ATTRIBUTES` column. This codebase still uses the `p_attribute_NN` parameters in PL/SQL calls (e.g., `p_attribute_01=>'REGION_SOURCE'` for DML processes, `p_attribute_01=>'{js_code}'` for dynamic actions). This works in 24.2 because the import API still accepts the positional form. Future APEX versions may require migration to `p_json_attributes`.

### CSP Nonces

APEX 24.2 enforces Content Security Policy for inline scripts. The `ui_tools.py` and `chart_tools.py` modules generate HTML/JS via PL/SQL region source (server-side rendering), which is CSP-compliant because the content is rendered by APEX itself. Client-side JS added via `apex_add_page_js()` / `apex_add_global_js()` is injected through the APEX page template's inline-code slots, which receive automatic CSP nonces.

### Theme Metadata Decoupling

APEX 24.2 decoupled theme metadata from the application export. Template IDs are workspace-specific and may differ between environments. The `templates.py` module ships hardcoded IDs for APEX 24.2.13 / Universal Theme 42 but provides `discover_template_ids()` to refresh them from the live database after `apex_connect()`. Always call discovery when targeting a different APEX instance or version.

### db.safe_col() for Version Safety

The `ConnectionManager.safe_col()` method checks whether a column exists in a data dictionary view before referencing it, with a cached lookup. This guards against column-not-found errors when querying `apex_application_*` views that may differ between APEX patch levels.

## Environment Variables

**Oracle Connection** (required): `ORACLE_DB_USER`, `ORACLE_DB_PASS`, `ORACLE_DSN`, `ORACLE_WALLET_DIR`, `ORACLE_WALLET_PASSWORD`

**APEX Config** (required): `APEX_WORKSPACE_ID`, `APEX_SCHEMA`, `APEX_WORKSPACE_NAME`

**Transport** (optional): `MCP_TRANSPORT` (stdio|streamable-http|sse), `MCP_HOST`, `MCP_PORT`, `MCP_PATH`

## Key Conventions

- All PL/SQL uses APEX internal import API (`wwv_flow_imp_page`, `wwv_flow_imp_shared`)
- Item names follow APEX convention: `P{page_id}_{COLUMN_NAME}`
- Templates target Universal Theme 42 (APEX 24.2)
- Template IDs are resolved dynamically via `templates.py` queries against `apex_application_temp_*` views
- Tool functions return JSON strings (not dicts) -- the MCP protocol handles serialization
- Default locale throughout demos and labels is pt-BR (Brazilian Portuguese)
- Default date format: `DD/MM/YYYY`, timestamp: `DD/MM/YYYY HH24:MI`
- APEX version constants: `24.2.13` (version), `24.2` (compat mode)

## Dependencies

Runtime: `fastmcp>=3.0.0`, `oracledb>=2.0.0`
Dev: `pytest>=8.0`
Python: `>=3.11`
Build: `hatchling`
No linter/formatter configured.

## Project Layout

```
apex_mcp/
  __init__.py          # Package init, version 0.3.0
  __main__.py          # python -m apex_mcp entry
  server.py            # FastMCP server, tool registration, CLI arg parsing
  config.py            # Env var loading, APEX version constants
  db.py                # ConnectionManager singleton
  session.py           # ImportSession singleton, component dataclasses
  ids.py               # IdGenerator singleton
  templates.py         # Universal Theme 42 template IDs + discovery
  themes.py            # Unimed CSS theme (palette #00995D)
  validators.py        # Input validation functions
  guards.py            # Pre-condition checks (connection, session, page)
  exceptions.py        # Domain exception hierarchy
  utils.py             # _esc, _blk, _json, _sql_to_varchar2
  tools/
    sql_tools.py       # connect, run_sql, status
    app_tools.py       # create/finalize/delete/export apps
    page_tools.py      # add/list pages
    component_tools.py # regions, items, buttons, processes, DAs
    shared_tools.py    # LOVs, auth schemes, nav, app items/processes
    schema_tools.py    # list/describe tables, detect relationships
    generator_tools.py # CRUD, dashboard, login generators
    user_tools.py      # create/list APEX users
    js_tools.py        # page JS, global JS, AJAX handlers
    inspect_tools.py   # read/update/delete existing components
    setup_tools.py     # setup guide, requirements, permissions
    validation_tools.py# item validations and computations
    visual_tools.py    # JET charts, gauges, funnels, sparklines, calendars
    devops_tools.py    # REST endpoints, export, docs, batch mode
    advanced_tools.py  # IG, master-detail, timeline, faceted search, etc.
    ui_tools.py        # 20 rich HTML visual components
    chart_tools.py     # 10 advanced chart types
demos/                 # Example build scripts (build_app100..209)
tests/                 # Unit + integration tests
.mcp.json              # MCP server configuration for IDE integration
pyproject.toml         # Build config (hatchling), entry point, pytest markers
```
