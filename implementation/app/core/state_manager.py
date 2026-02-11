from __future__ import annotations

from typing import Dict, Tuple

from app.schemas import EventImpactResult, UserState


class UserStateManager:
    AXES = ('money', 'time', 'energy', 'asset', 'reliability', 'identity')

    @staticmethod
    def calculate_scarcity_weights(state: UserState) -> Dict[str, float]:
        # g(x) = 1 / (1 + exp(-a*(x-b)))
        # using a lightweight piecewise approximation to avoid math overflow edge cases.
        weights: Dict[str, float] = {}
        for axis in UserStateManager.AXES:
            v = float(getattr(state, f'{axis}_value'))
            x = max(0.0, min(1.0, 1.0 - v))
            if x < 0.25:
                w = 0.15 + x * 0.8
            elif x < 0.5:
                w = 0.35 + (x - 0.25) * 1.2
            elif x < 0.75:
                w = 0.65 + (x - 0.5) * 1.2
            else:
                w = 0.95 + (x - 0.75) * 0.2
            weights[axis] = max(0.0, min(1.2, w))
        return weights

    @staticmethod
    def identify_main_constraint(state: UserState) -> str:
        weights = UserStateManager.calculate_scarcity_weights(state)
        return max(weights, key=weights.get)

    @staticmethod
    def update_axis_from_impact(state: UserState, impact: EventImpactResult, axis: str) -> Tuple[float, float]:
        old = float(getattr(state, f'{axis}_value'))
        delta = float(getattr(impact.impact_vector, f'delta_{axis}'))
        conf = float(getattr(impact.axis_confidence, axis))

        # Bayesian-like conservative update.
        alpha = 0.25 * max(0.1, min(1.0, conf))
        new_value = max(0.0, min(1.0, old + alpha * delta))
        new_conf = max(0.0, min(1.0, (float(getattr(state, f'{axis}_confidence')) + conf) / 2.0))
        return new_value, new_conf
