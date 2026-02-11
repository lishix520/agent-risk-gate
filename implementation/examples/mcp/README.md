# MCP Adapter E2E Demo

This demo calls the MCP adapter tool functions directly (which in turn call Continuity API).

## Prerequisites

1. Continuity API is running at `CONTINUITY_API_BASE_URL`.
2. Python deps installed in `implementation/`:

```bash
pip install -r requirements.txt
```

## Run

```bash
cd implementation
export CONTINUITY_API_BASE_URL=http://127.0.0.1:8000
export USER_ID=demo_user
python examples/mcp/run_adapter_e2e.py
```

What it covers:
- `continuity_health`
- `continuity_chat`
- optional `continuity_confirm_decision`
- `continuity_report_outcome`
- `continuity_get_state`
