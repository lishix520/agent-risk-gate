# Contributing

## Scope
- Focus on protocol clarity, runtime safety, and MCP compatibility.
- Avoid introducing hidden personalization or user profiling.

## How to contribute
1. Open an issue with a concrete problem statement.
2. Propose a minimal change that preserves the core invariants.
3. Add or update tests when behavior changes.

## Review bar
- Must not weaken continuity invariants.
- Must not bypass L4 risk gate behavior.
- Must not add user profiling or “personality” assumptions.

## Development
```bash
cd implementation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
make run
```

## Reporting security issues
Use `SECURITY.md` if present, otherwise open a private report to maintainers.
