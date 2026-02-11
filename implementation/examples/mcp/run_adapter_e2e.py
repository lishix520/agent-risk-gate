from __future__ import annotations

import asyncio
import json
import os
import time

from mcp_server import server


def _pretty(title: str, data: object) -> None:
    print(f'\n=== {title} ===')
    print(json.dumps(data, ensure_ascii=False, indent=2))


async def main() -> None:
    user_id = os.getenv('USER_ID', 'demo_user')
    idempotency_key = f'mcp-e2e-{int(time.time())}'

    health = await server.continuity_health()
    _pretty('health', health)

    chat = await server.continuity_chat(
        user_id=user_id,
        message='我刚刚误删了核心配置，可能需要强制回滚，风险很高。',
        idempotency_key=idempotency_key,
    )
    _pretty('chat', chat)

    trace = chat.get('trace', {})
    decision_id = trace.get('decision_id')
    if decision_id is None:
        raise RuntimeError('chat response missing trace.decision_id')

    high_risk = trace.get('high_risk_confirmation', {})
    if high_risk.get('required') and high_risk.get('confirm_token'):
        confirmed = await server.continuity_confirm_decision(
            decision_id=int(decision_id),
            user_id=user_id,
            confirm_token=high_risk['confirm_token'],
        )
        _pretty('confirm', confirmed)
    else:
        print('\n=== confirm ===\nskipped (not required)')

    outcome = await server.continuity_report_outcome(
        decision_id=int(decision_id),
        user_id=user_id,
        actual_impact_vector={
            'delta_money': 0.0,
            'delta_time': -0.1,
            'delta_energy': -0.1,
            'delta_asset': -0.2,
            'delta_reliability': -0.1,
            'delta_identity': 0.0,
        },
        actual_cost=0.45,
        continuity_failure=False,
        failure_type=None,
        user_visible_cost='一次额外沟通',
        preventable=True,
    )
    _pretty('outcome', outcome)

    state = await server.continuity_get_state(user_id=user_id)
    _pretty('state', state)


if __name__ == '__main__':
    asyncio.run(main())
