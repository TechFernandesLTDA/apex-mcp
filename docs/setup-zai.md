# apex-mcp — Setup with ZAI (Z.AI Vision)

> ZAI is a visual AI tool that complements apex-mcp.
> apex-mcp **builds** Oracle APEX apps; ZAI **sees and verifies** them.
> They work together — not as alternatives.

---

## Role Split

| Capability | apex-mcp | ZAI |
|------------|----------|-----|
| Create APEX pages | ✅ | ❌ |
| Add regions, items, buttons | ✅ | ❌ |
| Run SQL queries | ✅ | ❌ |
| Generate REST endpoints | ✅ | ❌ |
| See rendered UI screenshots | ❌ | ✅ |
| Verify layout looks correct | ❌ | ✅ |
| Diagnose rendering errors | ❌ | ✅ |
| Extract text from screenshots | ❌ | ✅ |
| Analyze data visualizations | ❌ | ✅ |

---

## Running Both Servers Together

Both MCP servers can run simultaneously in Claude Code (or any MCP-compatible client).

### `.mcp.json` with both servers

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
    },
    "zai": {
      "command": "npx",
      "args": ["-y", "zai-mcp-server"]
    }
  }
}
```

---

## Recommended Workflows

### Workflow 1: Build and Verify

```
1. [apex-mcp] apex_connect — connect to Oracle
2. [apex-mcp] apex_create_app(app_id=300, app_name="HR Portal") — create app
3. [apex-mcp] apex_generate_crud(table_name="EMPLOYEES") — generate pages
4. [apex-mcp] apex_finalize_app() — finalize
5. [ZAI] Take screenshot of the rendered app in APEX browser
6. [ZAI] analyze_image — verify layout, check for rendering issues
```

### Workflow 2: Debug Visual Issues

```
1. [ZAI] diagnose_error_screenshot(screenshot) — identify the error
2. [apex-mcp] apex_get_page_details(page_id=...) — inspect page config
3. [apex-mcp] apex_update_region(...) — fix the issue
4. [ZAI] analyze_image — confirm fix looks correct
```

### Workflow 3: Extract Data from Screenshots

```
1. [ZAI] extract_text_from_screenshot — get values from a chart or table
2. [apex-mcp] apex_run_sql — validate data against database
3. [ZAI] analyze_data_visualization — deeper chart analysis
```

---

## Tool Name Conflicts

apex-mcp and ZAI have distinct tool names — there are no conflicts.

| Server | Tool prefix pattern | Example |
|--------|---------------------|---------|
| apex-mcp | `apex_*` | `apex_add_page`, `apex_run_sql` |
| ZAI | descriptive names | `analyze_image`, `ui_diff_check` |

Claude and other AI clients will automatically route to the correct server based
on tool names.

---

## Installing ZAI

ZAI is available as an MCP server via npm:

```bash
npx -y zai-mcp-server
```

Or for permanent installation:

```bash
npm install -g zai-mcp-server
```

Check the [ZAI documentation](https://zai.ai/docs) for the latest setup instructions.

---

*pt-BR: Para configuração em português, veja o README principal.*
