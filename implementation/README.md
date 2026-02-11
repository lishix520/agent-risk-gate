# Continuity v1.1 Implementation Package

This package is a runnable skeleton aligned to the v1.1 docs.

## Included
- FastAPI runtime with idempotent `/chat`
- Subagent orchestration
- LLM-backed impact extraction with deterministic fallback
- PostgreSQL + pgvector schema
- Evidence/outcome audit loop
- Migration scripts and Makefile
- SuccessPath prioritized retrieval with constraint-aware ranking
- Pre-decision L4 risk gate (high-risk confirm flow)

## Quick start

```bash
cp .env.example .env

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

make db-up
uvicorn app.main:app --reload --port 8000
```

## Make targets
- `make install`
- `make run`
- `make test`
- `make compile`
- `make db-up`
- `make migrate`

## LLM provider
`ImpactExtractorAgent` supports:
- `LLM_PROVIDER=auto` (default)
- `LLM_PROVIDER=anthropic`
- `LLM_PROVIDER=openai`

If no provider/key is available, it falls back to deterministic extraction.

## API
- `POST /chat`
- `GET /user/{user_id}/state`
- `GET /user/{user_id}/objects`
- `GET /user/{user_id}/objects/shell/latest`
- `POST /user/{user_id}/objects/shell`
- `POST /user/{user_id}/objects/success-path`
- `POST /decision/{decision_id}/outcome?user_id=...`
- `POST /decision/{decision_id}/confirm`
- `GET /health`

## E2E demo
```bash
bash examples/e2e/run_curl_e2e.sh
```
Or set:
```bash
BASE_URL=http://127.0.0.1:8000 USER_ID=demo_user bash examples/e2e/run_curl_e2e.sh
```

## Migration
```bash
export DATABASE_URL=postgresql://...
bash scripts/apply_migrations.sh
```

Migration includes:
- `001_v1_1_to_v1_2.sql`
- `002_backfill_main_constraint.sql`
- `003_outcome_unique_per_decision.sql`
- `004_high_risk_confirmations.sql`

## Runtime behavior
- `/chat` now returns `trace.l4_gate` and `trace.best_success_path` when available.
- If L4 gate hits (`similarity >= L4_SIMILARITY_GATE`), execution is blocked pending explicit confirmation.
- `/chat` returns `trace.high_risk_confirmation.confirm_token`; use it in `/decision/{decision_id}/confirm`.

## MCP Adapter
```bash
export CONTINUITY_API_BASE_URL=http://127.0.0.1:8000
make run-mcp
```

MCP server module: `mcp_server.server`

Tools:
- `continuity_health`
- `continuity_chat`
- `continuity_confirm_decision`
- `continuity_report_outcome`
- `continuity_get_state`
- `continuity_list_objects`
- `continuity_get_latest_shell`
- `continuity_put_shell`
- `continuity_put_success_path`

## MCP client setup files
- `mcp_server/client_configs/claude_code.mcp.json`
- `mcp_server/client_configs/codex_desktop.mcp.json`
- `mcp_server/client_configs/generic_mcp.json`

## MCP adapter E2E demo
```bash
export CONTINUITY_API_BASE_URL=http://127.0.0.1:8000
make demo-mcp
```
