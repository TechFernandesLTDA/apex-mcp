# apex-mcp — Oracle APEX MCP Server

> Build, inspect, and modify **Oracle APEX 24.2** applications via natural language.
> Works with **Claude, GPT, Gemini, Cursor, VS Code**, and any MCP-compatible AI client.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-green)](https://github.com/jlowin/fastmcp)
[![Oracle APEX](https://img.shields.io/badge/Oracle_APEX-24.2-red)](https://apex.oracle.com)
[![Version](https://img.shields.io/badge/version-0.2.0-orange)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## Overview

**apex-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server
that exposes **86 tools** for building Oracle APEX 24.2 applications through AI assistants.
Built on FastMCP 3.x and Python 3.11+, it connects to Oracle Autonomous Database via the
`oracledb` thin driver (mTLS wallet — no Oracle Instant Client required).

Instead of navigating the APEX App Builder UI, you describe what you want and the AI does
the work: create apps, generate CRUD pages, add JET charts, configure auth schemes, export
pages, generate REST endpoints, and more.

```
┌─────────────────────────────────────────────────────────────────┐
│  AI Client (Claude / GPT / Gemini / Cursor / VS Code)           │
│                                                                  │
│  "Create a full HR app from the EMPLOYEES table"                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ MCP (stdio or HTTP)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  apex-mcp server (FastMCP 3.x, Python 3.11+)                    │
│  86 tools across 15 categories                                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ oracledb (mTLS)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Oracle Autonomous Database 23ai                                 │
│  wwv_flow_imp_page → APEX 24.2 App Builder                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Supported AI Clients

| Client | Transport | Config File | Setup Guide |
|--------|-----------|-------------|-------------|
| **Claude Code** | stdio | `.mcp.json` | [docs/setup-claude.md](docs/setup-claude.md) |
| **Claude Desktop** | stdio | `claude_desktop_config.json` | [docs/setup-claude.md](docs/setup-claude.md) |
| **GPT / OpenAI Agents SDK** | streamable-http | Python code | [docs/setup-gpt.md](docs/setup-gpt.md) |
| **Google Gemini CLI** | stdio | `.gemini/settings.json` | [docs/setup-gemini.md](docs/setup-gemini.md) |
| **Cursor IDE** | stdio | `.cursor/mcp.json` | [docs/setup-cursor.md](docs/setup-cursor.md) |
| **VS Code / GitHub Copilot** | stdio or http | `.vscode/mcp.json` | [docs/setup-vscode.md](docs/setup-vscode.md) |
| **ZAI (visual companion)** | n/a | side-by-side | [docs/setup-zai.md](docs/setup-zai.md) |

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/your-org/apex-mcp
cd apex-mcp
pip install -e .
```

### 2. Configure

Copy and edit the config file for your AI client:

**Claude Code** — create `.mcp.json` in your project root:
```json
{
  "mcpServers": {
    "apex-mcp": {
      "command": "python",
      "args": ["-m", "apex_mcp"],
      "cwd": "/path/to/apex-mcp",
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
    }
  }
}
```

For other clients see [Supported AI Clients](#supported-ai-clients) above.

### 3. Verify

In Claude Code:
```
/mcp
```
You should see `apex-mcp` connected with 86 tools.

Then:
```
Connect to Oracle and list all APEX applications in the workspace.
```

---

## Transport Modes

apex-mcp supports three transport modes, controlled via `--transport` flag or environment variables.

### stdio (default — local clients)

```bash
python -m apex_mcp                        # default
python -m apex_mcp --transport stdio      # explicit
apex-mcp                                  # if installed via pip
```

Best for: Claude Code, Claude Desktop, Cursor, VS Code, Gemini CLI.

### Streamable HTTP (remote / multi-client)

```bash
apex-mcp --transport streamable-http --port 8000
# Server available at: http://127.0.0.1:8000/mcp
```

Best for: OpenAI Agents SDK, Codespaces, remote setups, multiple clients.

### SSE (Server-Sent Events)

```bash
apex-mcp --transport sse --port 9000
# Server available at: http://127.0.0.1:9000/sse
```

Best for: clients that specifically require SSE transport.

### Environment Variables

All CLI flags have environment variable equivalents (lower priority than CLI args):

| Variable | CLI flag | Default |
|----------|----------|---------|
| `MCP_TRANSPORT` | `--transport` | `stdio` |
| `MCP_HOST` | `--host` | `127.0.0.1` |
| `MCP_PORT` | `--port` | `8000` |
| `MCP_PATH` | `--path` | `/mcp` (http) or `/sse` |

### Oracle Connection Variables

| Variable | Description |
|----------|-------------|
| `ORACLE_DB_USER` | Oracle schema name |
| `ORACLE_DB_PASS` | Oracle schema password |
| `ORACLE_DSN` | TNS alias or connect string |
| `ORACLE_WALLET_DIR` | Directory containing wallet files (`cwallet.sso`, etc.) |
| `ORACLE_WALLET_PASSWORD` | Wallet encryption password |
| `APEX_WORKSPACE_ID` | Numeric APEX workspace ID |
| `APEX_SCHEMA` | Schema that owns APEX objects |
| `APEX_WORKSPACE_NAME` | APEX workspace name |

---

## Tool Reference

86 tools across 15 categories.

### Connection & SQL
| Tool | Description |
|------|-------------|
| `apex_connect` | Connect to Oracle ADB (mTLS wallet) |
| `apex_run_sql` | Execute any SELECT/DML/DDL statement |
| `apex_status` | Show connection status and session info |

### Applications
| Tool | Description |
|------|-------------|
| `apex_create_app` | Create a new APEX application (starts import session) |
| `apex_finalize_app` | Finalize and commit the application |
| `apex_list_apps` | List all apps in the workspace |
| `apex_delete_app` | Delete an application |
| `apex_get_app_details` | Get full app configuration |
| `apex_validate_app` | Validate app structure (home page, orphan items, etc.) |
| `apex_dry_run_preview` | Toggle dry-run mode (log SQL without executing) |
| `apex_describe_page` | Describe a page's components in human-readable form |

### Pages
| Tool | Description |
|------|-------------|
| `apex_add_page` | Add a new page to the app |
| `apex_list_pages` | List all pages |
| `apex_get_page_details` | Get full page details |
| `apex_update_page` | Update page properties |
| `apex_delete_page` | Delete a page |
| `apex_copy_page` | Copy a page to a new ID |
| `apex_diff_app` | Compare app structure before/after changes |

### Regions & Components
| Tool | Description |
|------|-------------|
| `apex_add_region` | Add a region (HTML, IR, report, etc.) |
| `apex_list_regions` | List regions on a page |
| `apex_update_region` | Update region properties |
| `apex_delete_region` | Delete a region |
| `apex_add_interactive_grid` | Add an Interactive Grid region |
| `apex_add_master_detail` | Add a master-detail region pair |
| `apex_add_notification_region` | Add a notification/alert region |
| `apex_add_timeline` | Add a timeline region |
| `apex_add_breadcrumb` | Add a breadcrumb navigation region |
| `apex_add_faceted_search` | Add a faceted search region |
| `apex_add_file_upload` | Add a file upload component |
| `apex_add_search_bar` | Add a search bar component |

### Items (Form Fields)
| Tool | Description |
|------|-------------|
| `apex_add_item` | Add a form item (text, select, date, etc.) |
| `apex_list_items` | List items on a page |
| `apex_update_item` | Update item properties |
| `apex_delete_item` | Delete an item |
| `apex_bulk_add_items` | Add multiple items in one call |
| `apex_add_item_validation` | Add server-side validation to an item |
| `apex_add_item_computation` | Add a computation to set item value |

### Buttons & Processes
| Tool | Description |
|------|-------------|
| `apex_add_button` | Add a button to a page/region |
| `apex_delete_button` | Delete a button |
| `apex_add_process` | Add a page process (PL/SQL, DML, branch) |
| `apex_list_processes` | List page processes |

### Dynamic Actions
| Tool | Description |
|------|-------------|
| `apex_add_dynamic_action` | Add a dynamic action (client-side event handler) |
| `apex_list_dynamic_actions` | List dynamic actions on a page |

### Charts & Visualizations
| Tool | Description |
|------|-------------|
| `apex_add_jet_chart` | Add an Oracle JET chart (bar, line, pie, etc.) |
| `apex_add_gauge` | Add a gauge/dial chart |
| `apex_add_funnel` | Add a funnel chart |
| `apex_add_sparkline` | Add a sparkline chart |
| `apex_add_metric_cards` | Add metric/KPI cards with gradient styling |
| `apex_add_calendar` | Add a calendar region |
| `apex_add_chart_drilldown` | Add drill-down behavior to a chart |

### Shared Components
| Tool | Description |
|------|-------------|
| `apex_add_lov` | Add a List of Values (static or dynamic) |
| `apex_list_lovs` | List all LOVs in the app |
| `apex_add_auth_scheme` | Add an authorization scheme |
| `apex_list_auth_schemes` | List authorization schemes |
| `apex_add_nav_item` | Add a navigation menu item |
| `apex_add_app_item` | Add an application-level item (global variable) |
| `apex_add_app_process` | Add an application-level process |

### Schema Inspection
| Tool | Description |
|------|-------------|
| `apex_list_tables` | List Oracle tables/views in the schema |
| `apex_describe_table` | Describe columns, types, PKs, FKs (with cache) |
| `apex_detect_relationships` | Auto-detect FK relationships between tables |

### Generators (High-Level)
| Tool | Description |
|------|-------------|
| `apex_generate_crud` | Generate full CRUD (list + form pages) for a table |
| `apex_generate_dashboard` | Generate a dashboard with charts |
| `apex_generate_login` | Generate a login page |
| `apex_generate_report_page` | Generate a formatted report page |
| `apex_generate_wizard` | Generate a multi-step wizard |
| `apex_generate_analytics_page` | Generate an analytics page with multiple charts |
| `apex_generate_from_schema` | Generate a full app from multiple tables |
| `apex_generate_modal_form` | Generate a modal form dialog |
| `apex_generate_rest_endpoints` | Generate ORDS REST endpoints for tables |

### JavaScript
| Tool | Description |
|------|-------------|
| `apex_add_page_js` | Add page-level JavaScript |
| `apex_add_global_js` | Add app-level global JavaScript |
| `apex_add_global_css` | Add app-level CSS |
| `apex_add_page_css` | Add page-level CSS |
| `apex_generate_ajax_handler` | Generate an AJAX callback process |

### DevOps & Batch
| Tool | Description |
|------|-------------|
| `apex_export_page` | Export a page as SQL (for version control) |
| `apex_generate_docs` | Generate Markdown documentation for an app |
| `apex_begin_batch` | Begin a batch operation (queue multiple SQL statements) |
| `apex_commit_batch` | Execute the batch queue in one round-trip |
| `apex_preview_page` | Preview page structure (without opening browser) |

### Setup & Validation
| Tool | Description |
|------|-------------|
| `apex_setup_guide` | Get setup instructions for this workspace |
| `apex_check_requirements` | Verify all requirements are met |
| `apex_check_permissions` | Verify Oracle grants and APEX access |
| `apex_fix_permissions` | Auto-fix common permission issues |

### Users
| Tool | Description |
|------|-------------|
| `apex_create_user` | Create an APEX workspace user |
| `apex_list_users` | List workspace users |

---

## Code Examples

### Example 1: Full app from schema (single command)

```python
# Uses apex_generate_from_schema internally
# Prompt: "Generate a full app from tables EMPLOYEES, DEPARTMENTS, JOBS"
# Result: App with CRUD pages, dashboard, navigation — in ~10 seconds
```

### Example 2: Incremental build

```
1. apex_connect()
2. apex_create_app(app_id=200, app_name="Inventory", home_page=1)
3. apex_add_page(page_id=1, page_name="Dashboard", page_mode="Normal")
4. apex_add_region(page_id=1, region_name="KPIs", region_type="STATIC")
5. apex_add_metric_cards(page_id=1, region_id=..., metrics=[...])
6. apex_generate_crud(table_name="PRODUCTS", start_page_id=10)
7. apex_add_nav_item("Dashboard", app_id=200, page_id=1, icon="fa-home")
8. apex_add_nav_item("Products", app_id=200, page_id=10, icon="fa-box")
9. apex_finalize_app()
```

### Example 3: OpenAI Agents SDK

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    # apex-mcp must be running: apex-mcp --transport streamable-http
    async with MCPServerStreamableHttp(url="http://127.0.0.1:8000/mcp") as apex:
        agent = Agent(
            name="APEX Developer",
            instructions="Build Oracle APEX apps using apex-mcp tools.",
            mcp_servers=[apex],
        )
        result = await Runner.run(
            agent,
            "Connect to Oracle and generate a CRUD app for the ORDERS table."
        )
        print(result.final_output)

asyncio.run(main())
```

### Example 4: Batch operations

```
apex_begin_batch()
# ... add many regions, items, processes ...
apex_commit_batch(rollback_on_error=True)
# All statements execute in one round-trip; rolls back on any error
```

### Example 5: Dry-run mode

```
apex_dry_run_preview(enabled=True)
apex_generate_crud(table_name="EMPLOYEES")
# Logs all SQL without executing — useful for review before committing
apex_dry_run_preview(enabled=False)
```

---

## Architecture

```
apex_mcp/
├── server.py          Entry point — FastMCP 3.x, argparse (stdio/http/sse)
├── __main__.py        Enables `python -m apex_mcp`
├── __init__.py        Version: 0.2.0
├── config.py          Constants (APEX version, workspace ID, date format)
├── db.py              ConnectionManager singleton — mTLS, retry, batch, dry-run
├── ids.py             Sequential ID generator (base 8_900_000_000_000_000)
├── session.py         ImportSession — tracks pages, regions, items, buttons
├── templates.py       Hardcoded Universal Theme 42 template IDs
├── validators.py      Input validation (page IDs, SQL, chart types, table names)
├── utils.py           Shared helpers (_esc, _blk, _sql_to_varchar2)
└── tools/
    ├── sql_tools.py       apex_connect, apex_run_sql, apex_status
    ├── app_tools.py       apex_create_app, apex_finalize_app, ...
    ├── page_tools.py      apex_add_page, apex_list_pages
    ├── component_tools.py apex_add_region, apex_add_item, apex_add_button, ...
    ├── shared_tools.py    apex_add_lov, apex_add_auth_scheme, ...
    ├── schema_tools.py    apex_list_tables, apex_describe_table, ...
    ├── generator_tools.py apex_generate_crud, apex_generate_dashboard, ...
    ├── js_tools.py        apex_add_page_js, apex_add_global_js, ...
    ├── inspect_tools.py   apex_get_app_details, apex_update_*, apex_delete_*, ...
    ├── user_tools.py      apex_create_user, apex_list_users
    ├── setup_tools.py     apex_setup_guide, apex_check_requirements, ...
    ├── validation_tools.py apex_add_item_validation, apex_add_item_computation
    ├── visual_tools.py    apex_add_jet_chart, apex_add_gauge, ...
    ├── advanced_tools.py  apex_generate_report_page, apex_generate_wizard, ...
    └── devops_tools.py    apex_generate_rest_endpoints, apex_export_page, ...
```

### How APEX creation works

apex-mcp creates APEX applications by generating and executing `wwv_flow_imp_page.*`
PL/SQL calls directly against the Oracle database — the same mechanism used by APEX's
own import/export system. This bypasses the App Builder UI entirely and is fully
compatible with APEX 24.2.13 / Universal Theme 42.

### HTTP transport note

When using `--transport streamable-http` or `--transport sse`, apex-mcp is a
single-user server: the `ImportSession` singleton means only one active import
session exists at a time. For multi-user scenarios, run separate server instances
on different ports.

---

## Known Limitations

| Limitation | Details |
|------------|---------|
| Single import session | Only one `apex_create_app` → `apex_finalize_app` sequence at a time |
| No HTTP authentication | Bind HTTP transport to `127.0.0.1` (default); add a reverse proxy for remote access |
| APEX 24.2 only | `wwv_flow_imp_page` API is version-specific; not tested on APEX 23.x or 25.x |
| Oracle mTLS required | TLS direct connections are not supported (wallet required) |
| Licensed instrument content | `TEA_QUESTOES` / `TEA_OPCOES_RESPOSTA` tables are empty (content is licensed) |

---

## Requirements

| Component | Version |
|-----------|---------|
| Python | 3.11+ |
| FastMCP | 3.0.0+ |
| oracledb | 2.0.0+ |
| Oracle APEX | 24.2 (Universal Theme 42) |
| Oracle DB | 19c+ (tested on ADB 23ai) |
| Oracle Wallet | Required for mTLS connections |

No Oracle Instant Client required — the `oracledb` thin driver handles mTLS natively.

---

## Troubleshooting

### Connection issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ORA-12541: no listener` | Wrong DSN | Check `ORACLE_DSN` matches the TNS alias in `tnsnames.ora` |
| `ORA-28759: failure to open file` | Wrong wallet path | `ORACLE_WALLET_DIR` must contain `cwallet.sso` |
| `DPY-6005: cannot connect to database` | Wallet password wrong | Check `ORACLE_WALLET_PASSWORD` |
| `ModuleNotFoundError: apex_mcp` | Not installed | Run `pip install -e .` from apex-mcp directory |

### APEX issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ORA-20987: APEX - Application not found` | Wrong app_id or workspace | Check `APEX_WORKSPACE_ID` and run `apex_list_apps` |
| `ORA-01403: no data found` in item creation | Missing `p_attributes` on DatePicker | Fixed in v0.2.0 — update to latest |
| `PLS-00306: wrong number of arguments` | Wrong process parameter name | Use `p_process_success_message` not `p_success_message` |
| Buttons not showing on Standard pages | Wrong region position | Use content region positions (CLOSE/CREATE), not dialog footer |

### HTTP transport issues

| Problem | Solution |
|---------|----------|
| `ConnectionRefusedError` | Start server with `apex-mcp --transport streamable-http` first |
| `404 Not Found` at `/` | Default path is `/mcp`; use `curl http://127.0.0.1:8000/mcp` |
| OpenAI SDK can't connect | Ensure `MCPServerStreamableHttp` URL matches `--path` setting |

---

## Running Tests

```bash
cd apex-mcp
pip install -e ".[dev]"

# Unit tests (no database required)
pytest tests/ -v -m "not integration"

# All tests including integration (requires live Oracle connection)
pytest tests/ -v
```

The test suite has 51 unit tests covering tools, validators, and generators.

---

## Demo Scripts

| Script | Description |
|--------|-------------|
| `demos/build_app100.py` | TEA clinical assessment app (15 pages, 46 items) |
| `demos/build_app203.py` | Analytics dashboard with JET charts + metric cards |
| `demos/build_app204.py` | Backoffice from schema (8 tables, 17 pages, score 100/100) |
| `demos/build_app205.py` | Assessment wizard (4-step wizard, CRUD, dashboard, 9s build) |
| `demos/demo_rest_endpoints.py` | 5 tables → 25 ORDS endpoints in 1 second |
| `demos/demo_generate_docs.py` | Auto-generate Markdown docs for an app |

Run any demo (requires live Oracle connection):
```bash
python demos/build_app205.py
```

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new tools in `tests/`
4. Ensure `pytest tests/ -m "not integration"` passes
5. Submit a pull request

### Adding a new tool

1. Add the function to the appropriate `tools/*.py` module
2. Register it in `server.py` with `mcp.tool()(function_name)`
3. Add unit tests in `tests/`
4. Update the Tool Reference section in this README

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

*pt-BR: Este servidor MCP foi construído para o projeto Plataforma Desfecho TEA (Unimed Nacional),
usando Oracle APEX 24.2 + Oracle ADB 23ai. Para configuração detalhada do ambiente de produção,
consulte o `CLAUDE.md` na raiz do projeto.*
