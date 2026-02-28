# apex-mcp — Oracle APEX MCP Server

> Create, inspect, and modify **Oracle APEX 24.2** applications via natural language using Claude Code.

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://python.org)
[![FastMCP](https://img.shields.io/badge/FastMCP-3.x-green)](https://github.com/jlowin/fastmcp)
[![Oracle APEX](https://img.shields.io/badge/Oracle_APEX-24.2-red)](https://apex.oracle.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## What is this?

**apex-mcp** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that exposes **50 tools** for building Oracle APEX applications through AI. Instead of navigating the APEX App Builder UI, you describe what you want and Claude Code does the work.

```
"Create a CRUD for the EMPLOYEES table on pages 10 and 11, then add it to the nav menu"
→ apex_describe_table("EMPLOYEES")
→ apex_generate_crud("EMPLOYEES", 10, 11)
→ apex_add_nav_item("Employees", 10, 20, "fa-users")
```

---

## Features

| Category | Tools | Description |
|----------|-------|-------------|
| **Setup & Diagnostics** | 4 | Connection guide, requirements check, permission audit, fix grants |
| **Connection** | 3 | Connect to ADB, run SQL, check session state |
| **App Lifecycle** | 5 | Create/delete/list/finalize/export apps |
| **Pages** | 2 | Add pages (blank, form, report, login, dashboard, modal) |
| **Components** | 5 | Regions, items, buttons, processes, dynamic actions |
| **Shared Components** | 5 | LOVs, auth schemes, nav items, app items, app processes |
| **Schema Introspection** | 2 | List tables, describe table (columns, PKs, FKs, sequences) |
| **Generators** | 3 | Auto-generate CRUD, dashboard, login page |
| **JavaScript** | 3 | Page JS, global JS, AJAX handler generator |
| **Inspection & Editing** | 14 | Read/update/delete/diff existing app components |
| **Validations & Computations** | 2 | Item validations, item computations |
| **User Management** | 2 | Create/list APEX workspace users |

---

## Prerequisites

### 1. Oracle Autonomous Database

You need an Oracle Autonomous Database (ADB) instance.

1. In [Oracle Cloud Console](https://cloud.oracle.com), go to **Oracle Database → Autonomous Database**
2. Create or use an existing ADB instance (**Transaction Processing** recommended)
3. Click **DB Connection** → Download wallet → Extract to a local directory
4. Note the **wallet password** and the **DSN alias** from `tnsnames.ora` (e.g., `mydb_tp`)

### 2. Oracle APEX Workspace

1. Access APEX Admin at `https://<your-adb-host>/ords/apex_admin`
2. Create a Workspace and associate it with a database schema
3. Note the **Workspace ID**: Admin → Manage Workspaces → click workspace → see ID in URL
4. The schema user (e.g., `MY_SCHEMA`) must be the workspace-linked schema

### 3. Required Database Permissions

The schema user needs:

```sql
-- Minimum (auto-granted to workspace schemas):
-- CREATE SESSION, ALTER SESSION
-- SELECT on APEX_* views
-- EXECUTE on WWV_FLOW_IMP, WWV_FLOW_IMP_SHARED, WWV_IMP_WORKSPACE, WWV_FLOW_IMP_PAGE

-- For editing existing apps (apex_update_*, apex_delete_*):
-- Run as ADMIN or SYS:
GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_PAGE_PLUGS TO MY_SCHEMA;
GRANT SELECT, UPDATE, DELETE ON WWV_FLOW_STEP_ITEMS TO MY_SCHEMA;
GRANT SELECT, DELETE ON WWV_FLOW_STEPS TO MY_SCHEMA;
```

> **Note:** If your schema is the APEX workspace-linked schema, most permissions are already granted automatically. Use `apex_check_permissions()` to verify.

### 4. Python Environment

```bash
python --version   # Requires 3.11+
pip install fastmcp oracledb
```

---

## Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/TechFernandesLTDA/apex-mcp.git
cd apex-mcp/mcp-server
pip install -e .
```

### Step 2: Create `.mcp.json` in your project root

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

### Step 3: Verify in Claude Code

```
/mcp
```

You should see `apex-dev` with **50 tools**. If not, run `apex_check_requirements()` to diagnose.

---

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ORACLE_DB_USER` | Yes | Database username (workspace schema) | `MY_SCHEMA` |
| `ORACLE_DB_PASS` | Yes | Database password | `MyPass@2024` |
| `ORACLE_DSN` | Yes | TNS alias from `tnsnames.ora` | `mydb_tp` |
| `ORACLE_WALLET_DIR` | Yes | Path to extracted wallet directory | `/myproject/wallet` |
| `ORACLE_WALLET_PASSWORD` | Yes | Wallet decryption password | `wallet123` |
| `APEX_WORKSPACE_ID` | Yes | Numeric APEX workspace ID | `8822816515098715` |
| `APEX_SCHEMA` | Yes | Schema associated with APEX workspace | `MY_SCHEMA` |
| `APEX_WORKSPACE_NAME` | No | Workspace name | `MYWORKSPACE` |

### Finding your Workspace ID

In APEX Admin Console:
Admin → Manage Workspaces → [click your workspace] → ID shown in the page URL or details.

### Finding your DSN

Open `wallet/tnsnames.ora` — the alias names before `=` are your DSN options:
```
mydb_tp = (DESCRIPTION = ...)    ← use "mydb_tp" for OLTP (recommended for APEX)
mydb_high = (DESCRIPTION = ...)  ← high priority (analytics)
```

### Wallet directory contents

The extracted wallet folder must contain:
```
wallet/
├── tnsnames.ora       ← required
├── sqlnet.ora         ← required
├── cwallet.sso        ← required
├── ewallet.p12        ← required
├── ojdbc.properties
└── ...
```

> Do **not** point to the ZIP file — extract it first.

---

## Quick Start

Once connected in Claude Code, try these commands:

```python
# 1. Check setup
apex_setup_guide()           # Full setup documentation
apex_check_requirements()    # Verify installation
apex_check_permissions()     # Check DB permissions

# 2. Connect
apex_connect()               # Uses env vars automatically

# 3. Explore your schema
apex_list_tables()           # All tables in schema
apex_describe_table("EMPLOYEES")  # Columns, PKs, FKs

# 4. Create an app
apex_create_app(app_id=200, app_name="HR System")
apex_generate_login(page_id=101, app_name="HR System")
apex_add_page(1, "Dashboard", "blank")

# 5. Generate CRUD pages (automatic!)
apex_generate_crud("EMPLOYEES", 10, 11)
apex_generate_crud("DEPARTMENTS", 20, 21)

# 6. Add navigation
apex_add_nav_item("Dashboard", 1, 10, "fa-home")
apex_add_nav_item("Employees", 10, 20, "fa-users")
apex_add_nav_item("Departments", 20, 30, "fa-building")

# 7. Add authorization
apex_add_auth_scheme("IS_ADMIN",
    "return apex_util.get_session_state('APP_ROLE') = 'ADMIN';",
    "Admin access required.")

# 8. Finalize
apex_finalize_app()
```

Access your app at: `f?p=200` (relative to your APEX base URL)

---

## Tool Reference

### Setup & Diagnostics

| Tool | Description |
|------|-------------|
| `apex_setup_guide()` | Complete setup guide with all requirements |
| `apex_check_requirements()` | Verify packages, env vars, wallet, connectivity |
| `apex_check_permissions()` | Audit DB permissions for all MCP operations |

### Connection & Session

| Tool | Description |
|------|-------------|
| `apex_connect(user?, password?, dsn?, wallet_dir?, wallet_password?)` | Connect to Oracle ADB |
| `apex_run_sql(sql, max_rows?)` | Execute SELECT or PL/SQL |
| `apex_status()` | Current session state (app, pages, components built) |

### App Lifecycle

| Tool | Description |
|------|-------------|
| `apex_list_apps()` | List apps in the workspace |
| `apex_create_app(app_id, app_name, ...)` | Create app scaffold (theme + auth + nav) |
| `apex_finalize_app()` | Finalize import (must call when done!) |
| `apex_delete_app(app_id)` | Delete an application |

### Pages

| Tool | Description |
|------|-------------|
| `apex_add_page(page_id, page_name, page_type?, ...)` | Add page: blank/form/report/login/dashboard/modal |
| `apex_list_pages(app_id?)` | List pages via APEX dictionary |

### Components

| Tool | Description |
|------|-------------|
| `apex_add_region(page_id, region_name, region_type?, ...)` | Add region: static/ir/form/chart/plsql |
| `apex_add_item(page_id, region_name, item_name, item_type?, ...)` | Add form field |
| `apex_add_button(page_id, region_name, button_name, label, action?, ...)` | Add button |
| `apex_add_process(page_id, process_name, process_type?, ...)` | Add server process: dml/plsql/ajax |
| `apex_add_dynamic_action(page_id, da_name, event?, ...)` | Add Dynamic Action |

### Shared Components

| Tool | Description |
|------|-------------|
| `apex_add_lov(lov_name, lov_type?, sql_query?, static_values?)` | Create LOV |
| `apex_add_auth_scheme(scheme_name, function_body, error_message?, ...)` | Create auth scheme |
| `apex_add_nav_item(item_name, target_page, sequence?, icon?, ...)` | Add nav menu item |
| `apex_add_app_item(item_name, scope?, protection?)` | Create session-level variable |
| `apex_add_app_process(process_name, plsql_body, point?, ...)` | Create app-level process |

### Schema Introspection

| Tool | Description |
|------|-------------|
| `apex_list_tables(pattern?, include_columns?)` | List schema tables with columns |
| `apex_describe_table(table_name)` | Full table metadata: columns, PKs, FKs, indexes |

### Generators (High-Level)

| Tool | Description |
|------|-------------|
| `apex_generate_crud(table_name, list_page_id, form_page_id, ...)` | **Full CRUD**: IR list + form with DML, auto-inferred types |
| `apex_generate_dashboard(page_id, kpi_queries?, ir_sql?, ...)` | Dashboard with KPI cards + IR |
| `apex_generate_login(page_id?, app_name?, auth_process_plsql?, ...)` | Professional login page |

### JavaScript

| Tool | Description |
|------|-------------|
| `apex_add_page_js(page_id, javascript_code, js_file_urls?)` | Add inline JS to a page |
| `apex_add_global_js(function_name, javascript_code, ...)` | Generate reusable JS + upload instructions |
| `apex_generate_ajax_handler(page_id, callback_name, plsql_code, ...)` | Create AJAX endpoint + JS caller |

### Inspection & Editing (Existing Apps)

| Tool | Description |
|------|-------------|
| `apex_get_app_details(app_id)` | Full app metadata |
| `apex_get_page_details(app_id, page_id)` | All components on a page |
| `apex_list_regions(app_id, page_id)` | Regions list |
| `apex_list_items(app_id, page_id, region_name?)` | Items list |
| `apex_list_processes(app_id, page_id)` | Server processes |
| `apex_list_dynamic_actions(app_id, page_id)` | Dynamic Actions |
| `apex_list_lovs(app_id)` | Shared LOVs |
| `apex_list_auth_schemes(app_id)` | Auth schemes |
| `apex_update_region(app_id, page_id, region_name, ...)` | Update region properties |
| `apex_update_item(app_id, page_id, item_name, ...)` | Update item properties |
| `apex_delete_page(app_id, page_id)` | Delete a page |
| `apex_delete_region(app_id, page_id, region_name)` | Delete a region |
| `apex_copy_page(src_app, src_page, tgt_app, tgt_page, ...)` | Copy page between apps |

### User Management

| Tool | Description |
|------|-------------|
| `apex_create_user(username, password, email?, ...)` | Create APEX workspace user |
| `apex_list_users(workspace_id?)` | List workspace users |

---

## Demo Apps

The `demos/` directory contains three end-to-end build scripts that create real APEX applications. Each script runs in under 60 seconds and creates a fully functional app.

| Script | App ID | Description | Pages | Features Used |
|--------|--------|-------------|-------|---------------|
| `build_app200.py` | 200 | Clinic & Therapist Panel | 6 | Login, Dashboard KPIs, 2× CRUD, Nav |
| `build_app201.py` | 201 | Patient Registry | 5 | Login, Dashboard, CRUD, Validations, Computations, IR |
| `build_app202.py` | 202 | Admin & Audit | 6 | Login, Dashboard, CRUD, Auth Scheme, AJAX handler, Dynamic Action |

Run any demo against your own database:

```bash
# Edit the env vars at the top of the script, then:
python -X utf8 demos/build_app200.py
python -X utf8 demos/build_app201.py
python -X utf8 demos/build_app202.py
```

> **Note:** Use `-X utf8` on Windows to avoid encoding issues with special characters.

---

## CRUD Generator — How It Works

`apex_generate_crud` automatically:

1. **Introspects** the table (columns, types, PKs, FKs)
2. **Infers item types** from naming conventions:
   - `ID_*` (PK) → Hidden field
   - `ID_*` (FK) → Select list + auto LOV from parent table
   - `FL_*` → Yes/No switch
   - `DT_*` → Date picker (JET)
   - `DS_*` (> 500 chars) → Textarea
   - `DS_*` → Text field
   - `NR_*` → Number field
   - Audit columns → Skipped automatically
3. **Creates** an Interactive Report list page with "New" button
4. **Creates** a form page with all items, Save/Cancel/Delete buttons, and DML process
5. **Links** the IR to the form via detail link

> Works best with Oracle naming conventions (prefixed columns). For other schemas, Claude can adjust item types after generation using `apex_update_item`.

---

## APEX 24.2 API — Verified Parameters

All PL/SQL calls were verified against Oracle-supplied APEX 24.2 sample applications. Key differences from older documentation:

### `create_page`
- Use `p_page_template_options=>'#DEFAULT#'` — **not** `p_page_template_id`
- `p_step_template=>...` only for **login** pages
- `p_page_mode=>'MODAL'` only for **modal** pages — omit for normal pages
- No `p_last_updated_by` / `p_last_upd_yyyymmddhh24miss`

### `create_page_plug` / `create_page_item` / `create_page_process`
- No `p_flow_id`, `p_page_id`, `p_flow_step_id`, audit columns
- Autocomplete → `p_tag_attributes=>'autocomplete="username"'` (not `p_attributes=>wwv_flow_t_plugin_attribute_value`)
- `NATIVE_FORM_DML` requires `p_region_id=>wwv_flow_imp.id(...)` — handles INSERT/UPDATE/DELETE (no separate delete process)
- No `p_process_success_message` or `p_version_scn` in processes

### `create_page_validation`
- Type names: `ITEM_NOT_NULL` (not `ITEM_IS_NOT_NULL`), `ITEM_NOT_NULL_OR_ZERO`
- For `ITEM_NOT_NULL`: item name goes in `p_validation=>'P10_ITEM'` — **not** `p_associated_item`
- No `p_when_button_pressed` (invalid parameter)

### `create_page_process` (AJAX)
- `p_process_point=>'ON_DEMAND'` — **not** `'AJAX_CALLBACK'`

### `create_page_da_event` (Dynamic Action)
- Requires `p_event_sequence=>10`
- Item trigger: `p_triggering_element_type=>'ITEM'`, `p_triggering_element=>'P20_ITEM'`
- Omit `p_triggering_condition_type` when there is no condition
- No `p_fire_on_initialization` or `p_display_when_type` (invalid)

### `create_worksheet` (Interactive Report)
- `p_show_search_bar=>'Y'` / `'N'` — **not** `'YES'` / `'NO'`

### `create_list_item`
- No `p_version_scn`

---

## Architecture

```
mcp-server/
├── pyproject.toml
└── apex_mcp/
    ├── server.py          # FastMCP entry point (50 tools)
    ├── config.py          # Environment variables + defaults
    ├── db.py              # ConnectionManager singleton (mTLS + auto-reconnect)
    ├── ids.py             # Session-scoped unique ID generator
    ├── templates.py       # Universal Theme 42 template IDs
    ├── session.py         # Import session state tracking
    └── tools/
        ├── sql_tools.py       # apex_connect, apex_run_sql, apex_status
        ├── app_tools.py       # apex_create_app, apex_delete_app, ...
        ├── page_tools.py      # apex_add_page, apex_list_pages
        ├── component_tools.py # apex_add_region, apex_add_item, ...
        ├── shared_tools.py    # apex_add_lov, apex_add_auth_scheme, ...
        ├── schema_tools.py    # apex_list_tables, apex_describe_table
        ├── generator_tools.py # apex_generate_crud, apex_generate_dashboard, ...
        ├── js_tools.py        # apex_add_page_js, apex_generate_ajax_handler, ...
        ├── inspect_tools.py   # apex_get_page_details, apex_update_region, ...
        ├── user_tools.py      # apex_create_user, apex_list_users
        └── setup_tools.py     # apex_setup_guide, apex_check_requirements, ...
```

### Key Design Decisions

- **mTLS only**: Oracle Autonomous Database requires wallet-based connection (TLS direct mode not supported)
- **wwv_flow_imp_page.\***: Uses APEX 24.2 import API (not deprecated `wwv_flow_api.*`)
- **Session tracking**: `session.py` tracks created components to enable cross-referencing (e.g., region ID lookup by name when adding items)
- **ID generator**: Uses `time.time()`-salted sequential IDs to avoid conflicts with existing APEX components
- **Auto-reconnect**: `db.ping()` before each operation, reconnects transparently

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `DPI-1047: Cannot locate a 64-bit Oracle Client` | Old oracledb version | `pip install --upgrade oracledb` (uses thin mode, no client needed) |
| `ORA-28759: failure to open file` | Wallet path wrong | Point `ORACLE_WALLET_DIR` to the **extracted** folder, not the ZIP |
| `ORA-01017: invalid username/password` | Wrong credentials | Check `ORACLE_DB_USER` and `ORACLE_DB_PASS` |
| `TNS-03505: Failed to resolve name` | Wrong DSN alias | Open `wallet/tnsnames.ora`, copy an alias name exactly |
| `ORA-20987: Application does not exist` | Wrong workspace | Check `APEX_WORKSPACE_ID` matches your workspace |
| `ORA-01031: insufficient privileges` | Missing grants on WWV_ tables | Run the grant script in `apex_check_permissions()` output |
| `No module named 'apex_mcp'` | Wrong `cwd` in .mcp.json | Set `cwd` to the `mcp-server/` directory |
| `apex_finalize_app: no active session` | Forgot `apex_create_app` | Always call `apex_create_app()` before adding components |

---

## Best Practices Applied by This MCP

- **Naming**: Items prefixed `P{page}_` automatically
- **AJAX callbacks**: UPPERCASE names (APEX convention)
- **Authorization**: IS_ prefix schemes (IS_ADMIN, IS_MANAGER)
- **Sequences**: Multiples of 10 for easy future insertion
- **Security**: App items use RESTRICTED protection by default
- **DML**: Delete button shown only when editing existing record (PK not null)
- **Accessibility**: Required/optional label templates applied correctly
- **Audit columns**: Auto-excluded from generated forms (DT_CRIACAO, CREATED_ON, etc.)

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-tool`
3. Add your tool in `apex_mcp/tools/`
4. Register it in `apex_mcp/server.py`
5. Add docstring with APEX best practices
6. Submit a pull request

---

## License

MIT License — see [LICENSE](LICENSE)

---

## About

Built for Oracle APEX 24.2 + Universal Theme 42. Tested with Oracle Autonomous Database 23ai.

Inspired by the [ICHOM TEA project](https://github.com/TechFernandesLTDA) — clinical outcome tracking for ASD patients using APEX.
