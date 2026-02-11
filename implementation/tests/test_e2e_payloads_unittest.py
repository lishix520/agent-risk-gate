import json
import unittest
from pathlib import Path


class TestE2EPayloads(unittest.TestCase):
    def setUp(self) -> None:
        self.base = Path(__file__).resolve().parents[1] / 'examples' / 'e2e'

    def test_payload_files_are_valid_json(self) -> None:
        files = [
            '01_chat_request_high_risk.json',
            '01_chat_request_normal.json',
            '02_confirm_request_template.json',
            '03_outcome_request.json',
        ]
        for name in files:
            data = json.loads((self.base / name).read_text(encoding='utf-8'))
            self.assertIsInstance(data, dict)

    def test_chat_payload_has_required_fields(self) -> None:
        data = json.loads((self.base / '01_chat_request_high_risk.json').read_text(encoding='utf-8'))
        self.assertIn('user_id', data)
        self.assertIn('message', data)
        self.assertIn('idempotency_key', data)


if __name__ == '__main__':
    unittest.main()
