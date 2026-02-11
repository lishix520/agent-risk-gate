from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from app.schemas import AxisConfidence, EventImpactResult, ImpactVector
from app.subagents.base import SubagentResult
from app.subagents.llm_client import LLMClient, extract_json_block


class ImpactExtractorAgent:
    name = 'impact_extractor'

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.prompt_path = Path(__file__).resolve().parents[1] / 'prompts' / 'event_impact_v2_1.md'

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        message = str(payload.get('message', '')).strip()
        user_state = payload.get('user_state') or {}

        system_prompt = self.prompt_path.read_text(encoding='utf-8') if self.prompt_path.exists() else 'Return strict JSON only.'
        user_prompt = (
            'Extract EventImpact v2.1 JSON for this message. '\
            'Do not add markdown.\\n\\n'
            f'message: {message}\\n'
            f'user_state_baseline: {user_state}'
        )

        llm = await self.llm.json_completion(system_prompt, user_prompt)
        if llm.ok:
            parsed = extract_json_block(llm.text)
            if parsed:
                try:
                    obj = EventImpactResult.model_validate(parsed)
                    return SubagentResult(ok=True, data=obj.model_dump())
                except Exception as e:  # noqa: BLE001
                    return self._fallback(payload, f'llm_parse_failed:{e}')
            return self._fallback(payload, f'llm_no_json:{llm.provider}')

        return self._fallback(payload, f'llm_unavailable:{llm.error}')

    def _fallback(self, payload: Dict[str, Any], reason: str) -> SubagentResult:
        text = str(payload.get('message', ''))
        lower = text.lower()

        delta_time = -0.1 if any(k in lower for k in ['浪费', '重复', '重来', 'waste']) else 0.0
        delta_energy = -0.2 if any(k in lower for k in ['累', '烦', '挫败', 'frustrat']) else 0.0
        delta_reliability = -0.5 if any(k in lower for k in ['又', 'again', '忘', '不靠谱']) else 0.0
        delta_asset = -1.0 if any(k in lower for k in ['删库', '删除数据', 'data loss']) else 0.0
        delta_identity = 0.3 if any(k in lower for k in ['符合', '自主', '价值观']) else 0.0
        delta_money = -0.2 if any(k in lower for k in ['亏', '损失', '缺钱']) else 0.0

        missing_axes = []
        money_conf = 0.2 if delta_money == 0.0 else 0.7
        if money_conf <= 0.25:
            missing_axes.append('money')

        result = EventImpactResult(
            event_summary='auto-extracted impact from user message',
            event_class='generic_event',
            impact_vector=ImpactVector(
                delta_money=delta_money,
                delta_time=delta_time,
                delta_energy=delta_energy,
                delta_asset=delta_asset,
                delta_reliability=delta_reliability,
                delta_identity=delta_identity,
            ),
            axis_confidence=AxisConfidence(
                money=money_conf,
                time=0.7,
                energy=0.7,
                asset=0.8,
                reliability=0.8,
                identity=0.6,
            ),
            missing_axes=missing_axes,
            irreversible=(delta_asset <= -1.0),
            system_caused=any(k in lower for k in ['系统', 'assistant', '你又']),
            analysis_confidence=0.65,
            baseline_used={'has_user_state': bool(payload.get('user_state')), 'money_baseline_source': 'none'},
            evidence_spans=[],
            reasoning={'key_signals': [], 'implicit_info': [reason], 'impact_explanation': 'fallback extraction'},
        )
        return SubagentResult(ok=True, data=result.model_dump(), error=reason)
