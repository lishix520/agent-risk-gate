from app.core.cost_calculator import ContinuityCostCalculator
from app.schemas import AxisConfidence, EventImpactResult, ImpactVector, UserState


def test_memory_layer_thresholds() -> None:
    assert ContinuityCostCalculator.memory_layer(0.2) == 1
    assert ContinuityCostCalculator.memory_layer(0.5) == 2
    assert ContinuityCostCalculator.memory_layer(0.8) == 3
    assert ContinuityCostCalculator.memory_layer(1.2) == 4


def test_risk_vector_shape() -> None:
    impact = EventImpactResult(
        event_summary='x',
        event_class='x',
        impact_vector=ImpactVector(delta_money=-0.2),
        axis_confidence=AxisConfidence(),
    )
    vec = ContinuityCostCalculator.risk_vector(impact, 0.4)
    assert len(vec) == 8


def test_transfer_amplifier_rules() -> None:
    state = UserState(user_id='u1', time_value=0.3)
    impact = EventImpactResult(
        event_summary='x',
        event_class='x',
        impact_vector=ImpactVector(delta_asset=-0.8),
        axis_confidence=AxisConfidence(),
    )
    amps = ContinuityCostCalculator.transfer_amplifiers(impact, state)
    assert amps['energy'] >= 1.4
