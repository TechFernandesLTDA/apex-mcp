# apex-mcp — Setup for Cursor IDE

> Cursor supports MCP natively since version 0.43.
> apex-mcp works with any model available in Cursor (Claude, GPT-4o, etc.).

---

## Quick Setup

### 1. Open MCP Settings

In Cursor: `Cursor Settings` → `MCP` → `Add new global MCP server`

Or edit `.cursor/mcp.json` directly (already included in this repo).

### 2. Configure apex-mcp

The `.cursor/mcp.json` file in this repo is pre-configured with placeholders:

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

Replace all `YOUR_*` placeholders with your actual values.

### 3. Verify

In Cursor's chat panel, look for the MCP tools indicator. You can also type:

```
List all available APEX tools
```

Cursor will show which MCP tools it found.

---

## Global vs Project Config

| Scope | Location | Use when |
|-------|----------|----------|
| Project | `.cursor/mcp.json` (this file) | Working on this specific project |
| Global | `~/.cursor/mcp.json` | Using apex-mcp across multiple projects |

For global config, use the same format but set an absolute `cwd`.

---

## Using apex-mcp with Different Models

apex-mcp works with any model in Cursor — the tools are model-agnostic.
However, larger context models (Claude 3.5 Sonnet, GPT-4o) handle complex
multi-step APEX builds better due to the tool call volume.

### Recommended workflow in Cursor

1. Open the Chat panel (⌘L / Ctrl+L)
2. Select **Agent** mode (not Ask or Edit)
3. Start with: `Connect to Oracle and show me the current APEX apps`
4. Build incrementally: `Add a CRUD page for the PRODUCTS table`

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Server shows "error" | Check Cursor's MCP logs: `View → Output → MCP` |
| `python: not found` | Use full path: `"command": "/usr/bin/python3"` or your venv path |
| Tools appear but fail | Verify env vars — Oracle credentials must be correct |
| Works in Claude, not GPT | Some models handle tool schemas differently; try rephrasing the request |

---

*pt-BR: Para configuração em português, veja o README principal.*
