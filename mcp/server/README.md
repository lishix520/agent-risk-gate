# MCP Adapter

This folder provides an MCP server that adapts Continuity API endpoints into MCP tools.

## Tools

- `continuity_health`
- `continuity_chat`
- `continuity_confirm_decision`
- `continuity_report_outcome`
- `continuity_get_state`
- `continuity_list_objects`
- `continuity_get_latest_shell`
- `continuity_put_shell`
- `continuity_put_success_path`

## Trace fields to surface in host UI

For `continuity_chat`, surface these trace keys directly:
- `trace.l4_gate`
- `trace.high_risk_confirmation`
- `trace.best_success_path`
- `trace.reality_first`

`trace.reality_first` is a low-intervention reality-check hint, not a personality diagnosis.

## Run

```bash
cd implementation
export CONTINUITY_API_BASE_URL=http://127.0.0.1:8000
python -m mcp_server.server
```

## Environment

- `CONTINUITY_API_BASE_URL` (default: `http://127.0.0.1:8000`)
- `CONTINUITY_MCP_HTTP_TIMEOUT` (default: `20`)

## MCP client config example

```json
{
  "mcpServers": {
    "continuity": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/ABS/PATH/TO/implementation",
      "env": {
        "CONTINUITY_API_BASE_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

## Client config files

- `mcp_server/client_configs/claude_code.mcp.json`
- `mcp_server/client_configs/codex_desktop.mcp.json`
- `mcp_server/client_configs/generic_mcp.json`

Use the generic file as baseline for other hosts (including antigravity-like runtimes) that support standard MCP server declarations.
