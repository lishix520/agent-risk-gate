# Continuity Kernel

AI Compliance & Risk Gating + Cost-Aware Agent Kernel

A continuity-first runtime for agent systems. It optimizes collaboration stability under real-world constraints, not just completion rates.

## What This Is
- Risk-gated runtime with low-intervention reality checks
- Minimal long-term objects: `Shell` and `SuccessPath`
- MCP adapter for Claude Code, Codex, and other MCP hosts

## What This Is Not
- A generic “memory product”
- A chat bot optimized for engagement

## Core Principles
1. Continuity is invariant, not an optimization target.
2. Reality is the decision boundary, not historical shell.
3. User instruction is respected within continuity + reality constraints.
4. No forced persuasion; only low-intervention hints unless high risk.

## Quick Start
```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make db-up
make run
```

## MCP Adapter
```bash
export CONTINUITY_API_BASE_URL=http://127.0.0.1:8000
make run-mcp
```

## Repo Layout
See `REPO_STRUCTURE.md`.

## License
MIT (recommended for maximum adoption).
