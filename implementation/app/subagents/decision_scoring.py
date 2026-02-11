from __future__ import annotations

from typing import Any, Dict, List

from app.subagents.base import SubagentResult


class DecisionScoringAgent:
    name = 'decision_scoring'

    @staticmethod
    def _layer_multiplier(layer: int) -> float:
        if layer <= 1:
            return 1.0
        if layer == 2:
            return 5.0
        if layer == 3:
            return 30.0
        return 120.0

    async def run(self, payload: Dict[str, Any]) -> SubagentResult:
        predicted_gain = float(payload.get('predicted_gain', 0.0))
        predicted_cost = float(payload.get('predicted_cost', 0.0))
        uncertainty_penalty = float(payload.get('uncertainty_penalty', 0.0))
        memories: List[Dict[str, Any]] = list(payload.get('similar_memories') or [])

        memory_penalty = 0.0
        for m in memories:
            w = float(m.get('memory_weight', 0.0))
            s = float(m.get('similarity', 0.0))
            layer = int(m.get('memory_layer', 1))
            memory_penalty += w * s * self._layer_multiplier(layer)

        predicted_risk = predicted_cost + memory_penalty
        score = predicted_gain - predicted_risk - uncertainty_penalty

        return SubagentResult(
            ok=True,
            data={
                'score': score,
                'predicted_gain': predicted_gain,
                'predicted_risk': predicted_risk,
                'memory_penalty': memory_penalty,
                'uncertainty_penalty': uncertainty_penalty,
            },
        )
