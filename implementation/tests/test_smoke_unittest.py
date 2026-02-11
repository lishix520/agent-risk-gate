import unittest

from app.core.cost_calculator import ContinuityCostCalculator
from app.schemas import AxisConfidence, EventImpactResult, ImpactVector, UserState
from app.subagents.constraint_intake import ConstraintIntakeAgent


class TestSmoke(unittest.TestCase):
    def test_memory_layer_thresholds(self) -> None:
        self.assertEqual(ContinuityCostCalculator.memory_layer(0.2), 1)
        self.assertEqual(ContinuityCostCalculator.memory_layer(0.5), 2)
        self.assertEqual(ContinuityCostCalculator.memory_layer(0.8), 3)
        self.assertEqual(ContinuityCostCalculator.memory_layer(1.2), 4)

    def test_risk_vector_shape(self) -> None:
        impact = EventImpactResult(
            event_summary='x',
            event_class='x',
            impact_vector=ImpactVector(delta_money=-0.2),
            axis_confidence=AxisConfidence(),
        )
        vec = ContinuityCostCalculator.risk_vector(impact, 0.4)
        self.assertEqual(len(vec), 8)

    def test_transfer_amplifier_rules(self) -> None:
        state = UserState(user_id='u1', time_value=0.3)
        impact = EventImpactResult(
            event_summary='x',
            event_class='x',
            impact_vector=ImpactVector(delta_asset=-0.8),
            axis_confidence=AxisConfidence(),
        )
        amps = ContinuityCostCalculator.transfer_amplifiers(impact, state)
        self.assertGreaterEqual(amps['energy'], 1.4)

    def test_shell_bias_detection_hit_without_reality_signal(self) -> None:
        r = ConstraintIntakeAgent.detect_shell_bias('我们一直这样做，要不要继续沿用？')
        self.assertTrue(r['hit'])
        self.assertFalse(r['has_reality_signal'])
        self.assertGreaterEqual(len(r['questions']), 1)

    def test_shell_bias_detection_no_hit_with_reality_signal(self) -> None:
        r = ConstraintIntakeAgent.detect_shell_bias('我们一直这样做，但现在预算只有1000，期限7天。')
        self.assertFalse(r['hit'])
        self.assertTrue(r['has_reality_signal'])


if __name__ == '__main__':
    unittest.main()
