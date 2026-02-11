from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class SubagentResult:
    ok: bool
    data: Dict[str, Any]
    error: str | None = None


class Subagent(Protocol):
    name: str

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        ...
