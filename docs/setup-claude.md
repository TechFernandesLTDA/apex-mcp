# apex-mcp — Setup for Claude (Code & Desktop)

> Claude Code and Claude Desktop support MCP natively via stdio.
> This is the primary tested configuration for apex-mcp.

---

## Claude Code (CLI)

### 1. Install apex-mcp

```bash
cd /path/to/apex-mcp
pip install -e .
```

### 2. Create `.mcp.json` in your project root

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

> The `.mcp.json` file at the root of the folder you open in Claude Code is
> automatically picked up. No additional configuration is needed.

### 3. Verify

Open Claude Code in your project directory and run:

```
/mcp
```

You should see `apex-mcp` listed with status `connected` and 86 tools available.

### 4. First use

```
Connect to the Oracle database and show me the available APEX applications.
```

Claude will call `apex_connect` → `apex_list_apps` automatically.

---

## Claude Desktop

### 1. Locate the config file

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

### 2. Add apex-mcp to the config

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

### 3. Restart Claude Desktop

The MCP server starts with Claude Desktop. Look for the hammer icon (🔨) in the
chat interface — it indicates available tools.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `/mcp` shows no servers | Check that `.mcp.json` is in the working directory where you launched Claude Code |
| `ModuleNotFoundError: apex_mcp` | Run `pip install -e .` from the `mcp-server/` directory |
| `ORA-12541: no listener` | Check `ORACLE_DSN` and wallet path; mTLS requires wallet files |
| `ORA-28759: failure to open file` | `ORACLE_WALLET_DIR` must point to the directory containing `cwallet.sso` |
| Tool calls time out | Database is idle; call `apex_connect` first to warm up the connection |
| Server disconnects mid-session | Normal for long idle periods; apex-mcp auto-reconnects on the next tool call |

---

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `ORACLE_DB_USER` | Oracle schema name | `TEA_APP` |
| `ORACLE_DB_PASS` | Oracle schema password | `MyPass@2024` |
| `ORACLE_DSN` | TNS alias or connect string | `mydb_tp` |
| `ORACLE_WALLET_DIR` | Directory with wallet files | `/opt/wallet` |
| `ORACLE_WALLET_PASSWORD` | Wallet password | `walletpw` |
| `APEX_WORKSPACE_ID` | Numeric APEX workspace ID | `8822816515098715` |
| `APEX_SCHEMA` | Schema that owns APEX objects | `TEA_APP` |
| `APEX_WORKSPACE_NAME` | APEX workspace name | `TEA` |

---

*pt-BR: Para configuração em português, veja o README principal.*
