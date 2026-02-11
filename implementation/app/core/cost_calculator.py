from __future__ import annotations

from typing import Dict

from app.schemas import EventImpactResult, UserState


class ContinuityCostCalculator:
    AXES = ('money', 'time', 'energy', 'asset', 'reliability', 'identity')

    @staticmethod
    def transfer_amplifiers(impact: EventImpactResult, state: UserState) -> Dict[str, float]:
        amps = {axis: 1.0 for axis in ContinuityCostCalculator.AXES}

        if impact.impact_vector.delta_asset <= -0.6 and state.time_value <= 0.4:
            amps['energy'] = max(amps['energy'], 1.4)

        if impact.impact_vector.delta_money <= -0.4 and state.identity_value <= 0.5:
            amps['identity'] = max(amps['identity'], 1.3)

        if impact.system_caused and impact.impact_vector.delta_reliability < 0:
            amps['reliability'] = max(amps['reliability'], 1.5)

        return amps

    @staticmethod
    def calculate(impact: EventImpactResult, scarcity_weights: Dict[str, float], state: UserState) -> float:
        amps = ContinuityCostCalculator.transfer_amplifiers(impact, state)
        cost = 0.0
        for axis in ContinuityCostCalculator.AXES:
            delta_abs = abs(float(getattr(impact.impact_vector, f'delta_{axis}')))
            w = float(scarcity_weights.get(axis, 0.5))
            a = float(amps.get(axis, 1.0))
            cost += delta_abs * w * a

        # Physical irreversibility multiplier.
        if impact.irreversible:
            cost *= 5.0

        return max(0.0, min(10.0, cost))

    @staticmethod
    def memory_layer(cost: float) -> int:
        if cost < 0.3:
            return 1
        if cost < 0.7:
            return 2
        if cost < 0.9:
            return 3
        return 4

    @staticmethod
    def memory_weight(cost: float, irreversible: bool) -> float:
        w = cost * (1.5 if irreversible else 1.0)
        return max(0.0, min(1.0, w))

    @staticmethod
    def risk_vector(impact: EventImpactResult, cost: float) -> list[float]:
        return [
            abs(impact.impact_vector.delta_money),
            abs(impact.impact_vector.delta_time),
            abs(impact.impact_vector.delta_energy),
            abs(impact.impact_vector.delta_asset),
            abs(impact.impact_vector.delta_reliability),
            abs(impact.impact_vector.delta_identity),
            cost,
            1.0 if impact.irreversible else 0.0,
        ]
