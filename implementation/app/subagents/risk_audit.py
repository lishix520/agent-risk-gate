from __future__ import annotations

from typing import Any, Dict, List

from app.subagents.base import SubagentResult


class RiskAuditAgent:
    name = 'risk_audit'

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        had_success_path = bool(payload.get('had_success_path', False))
        used_success_path = bool(payload.get('used_success_path', False))
        asked_before_try = bool(payload.get('asked_before_try', True))
        user_repeated_context = bool(payload.get('user_repeated_context', False))
        hallucinated = bool(payload.get('hallucinated', False))

        failures: List[str] = []
        if had_success_path and not used_success_path:
            failures.append('success_path_not_reused')
        if not asked_before_try:
            failures.append('asked_should_have_asked')
        if user_repeated_context:
            failures.append('lost_context')
        if hallucinated:
            failures.append('hallucinated_continuity')

        return SubagentResult(
            ok=True,
            data={
                'continuity_failures': failures,
                'should_clarify_first': len(failures) > 0,
            },
        )
