# apex-mcp — Setup for Google Gemini

> Gemini CLI and Google ADK both support MCP servers.
> apex-mcp works via **stdio** (Gemini CLI) or **HTTP** (Google ADK).

---

## Option A: Gemini CLI

### 1. Install Gemini CLI

```bash
npm install -g @google/gemini-cli
# or: pip install gemini-cli
```

### 2. Configure apex-mcp

The Gemini CLI reads MCP config from `.gemini/settings.json` in your project root
(already included in this repo as `.gemini/settings.json`).

Create or edit `~/.gemini/settings.json` for global config:

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

### 3. Verify

```bash
gemini
# In the chat:
> /mcp list
# Should show apex-mcp with 86 tools
```

### 4. FastMCP shortcut

If you have `fastmcp` installed:

```bash
fastmcp install gemini-cli /path/to/apex-mcp/apex_mcp/server.py
```

This auto-configures Gemini CLI to use apex-mcp.

---

## Option B: Gemini CLI with HTTP (remote server)

If apex-mcp is running on a remote machine or in a container:

```json
{
  "mcpServers": {
    "apex-mcp": {
      "httpUrl": "http://your-server:8000/mcp"
    }
  }
}
```

Start the server with:

```bash
apex-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

> **Security:** Binding to `0.0.0.0` exposes the server on all interfaces.
> Add a reverse proxy with authentication for production use.

---

## Option C: Google ADK (Python)

```python
import asyncio
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

async def main():
    toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=["-m", "apex_mcp"],
            env={
                "ORACLE_DB_USER": "YOUR_SCHEMA",
                "ORACLE_DB_PASS": "YOUR_PASSWORD",
                "ORACLE_DSN": "YOUR_DSN",
                "ORACLE_WALLET_DIR": "/path/to/wallet",
                "ORACLE_WALLET_PASSWORD": "YOUR_WALLET_PW",
                "APEX_WORKSPACE_ID": "YOUR_WORKSPACE_ID",
                "APEX_SCHEMA": "YOUR_SCHEMA",
                "APEX_WORKSPACE_NAME": "YOUR_WORKSPACE",
            }
        )
    )

    agent = Agent(
        model="gemini-2.0-flash",
        name="apex_developer",
        instruction="Build Oracle APEX applications using the available tools.",
        tools=[toolset],
    )

    # The toolset lifecycle is managed by the agent runner
    async with toolset:
        result = await agent.run("Connect to Oracle and list all APEX apps.")
        print(result)

asyncio.run(main())
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `MCP server not found` | Verify `cwd` points to the directory containing `apex_mcp/` |
| Tools not listed | Check Python is in PATH; try `python --version` |
| `ModuleNotFoundError` | Run `pip install -e .` from the apex-mcp directory |
| HTTP connection refused | Start server with `apex-mcp --transport streamable-http` |

---

*pt-BR: Para configuração em português, veja o README principal.*
