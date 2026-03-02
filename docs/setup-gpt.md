# apex-mcp — Setup for GPT / OpenAI

> OpenAI's tooling supports MCP via **Streamable HTTP** transport.
> You need to run apex-mcp as an HTTP server before connecting.

---

## Option A: OpenAI Agents SDK (Python)

This is the recommended integration path for automated workflows.

### 1. Start apex-mcp in HTTP mode

```bash
cd /path/to/apex-mcp
export ORACLE_DB_USER=YOUR_SCHEMA
export ORACLE_DB_PASS=YOUR_PASSWORD
export ORACLE_DSN=YOUR_DSN
export ORACLE_WALLET_DIR=/path/to/wallet
export ORACLE_WALLET_PASSWORD=YOUR_WALLET_PW
export APEX_WORKSPACE_ID=YOUR_WORKSPACE_ID
export APEX_SCHEMA=YOUR_SCHEMA
export APEX_WORKSPACE_NAME=YOUR_WORKSPACE

apex-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

The server starts at `http://127.0.0.1:8000/mcp`.

### 2. Install the OpenAI Agents SDK

```bash
pip install openai-agents
```

### 3. Connect from Python

```python
import asyncio
from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

async def main():
    # Connect to the running apex-mcp server
    async with MCPServerStreamableHttp(url="http://127.0.0.1:8000/mcp") as apex:
        agent = Agent(
            name="APEX Developer",
            instructions=(
                "You are an Oracle APEX developer. Use the apex-mcp tools "
                "to build and modify APEX applications. Always call apex_connect "
                "before any database operation."
            ),
            mcp_servers=[apex],
        )
        result = await Runner.run(
            agent,
            "Connect to the database and list all APEX applications."
        )
        print(result.final_output)

asyncio.run(main())
```

### 4. Multi-turn example

```python
async def build_crud_app():
    async with MCPServerStreamableHttp(url="http://127.0.0.1:8000/mcp") as apex:
        agent = Agent(
            name="APEX Builder",
            instructions="Build Oracle APEX applications using apex-mcp tools.",
            mcp_servers=[apex],
        )
        runner = Runner()

        # Step 1: connect
        await runner.run(agent, "Connect to Oracle and verify connection status.")

        # Step 2: create app
        await runner.run(agent, "Create a new APEX app with ID 300, name 'HR Portal'.")

        # Step 3: generate CRUD
        await runner.run(agent, "Generate a CRUD page for the EMPLOYEES table.")

        # Step 4: finalize
        result = await runner.run(agent, "Finalize the application.")
        print(result.final_output)

asyncio.run(build_crud_app())
```

---

## Option B: ChatGPT Desktop

ChatGPT Desktop (macOS/Windows) supports MCP as of late 2024. The configuration
format is similar to Claude Desktop.

> **Note:** ChatGPT Desktop MCP support is evolving. Check the
> [OpenAI documentation](https://platform.openai.com/docs) for the latest status.

### Config location

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/ChatGPT/mcp_config.json` |
| Windows | `%APPDATA%\ChatGPT\mcp_config.json` |

### Config format (stdio)

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

---

## Option C: GitHub Copilot

GitHub Copilot uses the VS Code MCP integration. See [setup-vscode.md](setup-vscode.md).

---

## Known Limitations with OpenAI

| Limitation | Details |
|------------|---------|
| HTTP required | OpenAI Agents SDK does not support stdio; use `--transport streamable-http` |
| Single user | apex-mcp's session singleton means only one active import session at a time |
| No streaming tool output | Results are returned as complete JSON; large outputs may be truncated |
| Authentication | apex-mcp HTTP server has no auth layer — bind to `127.0.0.1` (default) |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ConnectionRefusedError` | Start `apex-mcp --transport streamable-http` first |
| `404 Not Found` | Default path is `/mcp`; verify with `curl http://127.0.0.1:8000/mcp` |
| Tool list empty | The HTTP handshake may have failed; check server logs |
| `ORA-` errors in tool response | These are Oracle database errors — check credentials and wallet |

---

*pt-BR: Para configuração em português, veja o README principal.*
