# apex-mcp — Setup for VS Code / GitHub Copilot

> VS Code added MCP support (GA) in July 2025 via the GitHub Copilot extension.
> apex-mcp works in **Copilot Agent Mode** with all 86 tools.

---

## Prerequisites

- VS Code 1.93+
- GitHub Copilot extension with Copilot Chat enabled
- Copilot Agent Mode enabled (check Settings → Copilot → Agent Mode)

---

## Configuration

### Important: VS Code uses a different format

VS Code's `.vscode/mcp.json` uses `"servers"` (not `"mcpServers"`) and requires
a `"type"` field. This is **different** from Claude, Cursor, and Gemini.

The `.vscode/mcp.json` file in this repo uses the correct format:

```json
{
  "servers": {
    "apex-mcp": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "apex_mcp"],
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

> VS Code also accepts `"type": "http"` with a `"url"` field for HTTP mode.

### Setup steps

1. Edit `.vscode/mcp.json` in this repo with your credentials
2. Open VS Code in the apex-mcp directory
3. VS Code will prompt to enable the MCP server — click **Enable**
4. Open Copilot Chat (Ctrl+Alt+I) and switch to **Agent** mode

---

## Using apex-mcp in Copilot Agent Mode

In Copilot Chat with Agent mode selected:

```
@apex-mcp Connect to Oracle and show me all APEX applications
```

Or without the `@` mention (Copilot auto-routes to available MCP tools):

```
List all tables in the Oracle schema and generate CRUD pages for EMPLOYEES
```

### Example multi-step workflow

```
1. Connect to Oracle database
2. List all APEX apps in workspace TEA
3. Get details for app 100
4. Add a new page 25 with an Interactive Report on the ORDERS table
5. Verify the page was created
```

---

## Codespaces / Remote Development

For VS Code remote or GitHub Codespaces, use HTTP transport instead:

### In the Codespace terminal:

```bash
ORACLE_DB_USER=YOUR_SCHEMA \
ORACLE_DB_PASS=YOUR_PASSWORD \
ORACLE_DSN=YOUR_DSN \
ORACLE_WALLET_DIR=/path/to/wallet \
ORACLE_WALLET_PASSWORD=YOUR_WALLET_PW \
APEX_WORKSPACE_ID=YOUR_WORKSPACE_ID \
APEX_SCHEMA=YOUR_SCHEMA \
APEX_WORKSPACE_NAME=YOUR_WORKSPACE \
apex-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

### In `.vscode/mcp.json`:

```json
{
  "servers": {
    "apex-mcp": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No tools shown in Agent mode | Check VS Code Output → MCP for errors |
| `"servers" not recognized` | Ensure VS Code 1.93+ and Copilot extension is updated |
| `"type" is required` | VS Code rejects configs without `"type": "stdio"` or `"type": "http"` |
| Tools visible but fail | Check env vars — Oracle wallet path must be absolute |
| Works locally, not in remote | Use HTTP transport for remote connections (see above) |

---

## Format Comparison

| Client | Top-level key | Type field |
|--------|--------------|-----------|
| VS Code | `"servers"` | Required (`"stdio"` or `"http"`) |
| Claude Code | `"mcpServers"` | Not used |
| Cursor | `"mcpServers"` | Not used |
| Gemini | `"mcpServers"` | Not used |

---

*pt-BR: Para configuração em português, veja o README principal.*
