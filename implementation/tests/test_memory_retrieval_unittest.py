import unittest

from app.subagents.memory_retrieval import MemoryRetrievalAgent


class TestMemoryRetrievalRanking(unittest.TestCase):
    def test_score_success_path_prefers_slot_and_intent_match(self) -> None:
        row_good = {
            'name': 'notes_read_title',
            'confidence': 'high',
            'updated_at': '2026-02-07T01:00:00+00:00',
            'payload_json': {
                'intent': 'read apple notes by title',
                'required_slots': ['target', 'environment', 'success_criteria'],
                'tags': ['notes', 'execution'],
                'procedure': 'osascript ...',
            },
        }
        row_bad = {
            'name': 'generic_discuss',
            'confidence': 'low',
            'updated_at': '2025-01-01T01:00:00+00:00',
            'payload_json': {
                'intent': 'general discussion',
                'required_slots': ['purpose'],
                'tags': ['chat'],
                'procedure': 'none',
            },
        }

        scored_good = MemoryRetrievalAgent._score_success_path(
            row_good,
            intent_query='please read notes title xxx',
            required_slots=['target', 'environment', 'success_criteria'],
            main_constraint='time',
        )
        scored_bad = MemoryRetrievalAgent._score_success_path(
            row_bad,
            intent_query='please read notes title xxx',
            required_slots=['target', 'environment', 'success_criteria'],
            main_constraint='time',
        )
        self.assertGreater(scored_good['retrieval_score'], scored_bad['retrieval_score'])

    def test_extract_failure_features(self) -> None:
        features = MemoryRetrievalAgent._extract_failure_features('系统又忘了，可能删库和上下文丢失，风险很高')
        self.assertIn('system_error', features)
        self.assertIn('data_loss', features)
        self.assertIn('context_loss', features)
        self.assertIn('high_risk', features)


if __name__ == '__main__':
    unittest.main()
