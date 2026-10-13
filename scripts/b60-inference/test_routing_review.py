import json
from pathlib import Path
import unittest
from routing_review import review

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / 'docs/projects/AI Projects/benchmarks/ask-routing-development-v1'


class RoutingReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = (ROOT / 'scripts/aster-adaptive/fixtures/routing-families-v1.json').read_bytes()
        self.run = (ROOT / 'docs/projects/AI Projects/experiments/m3-9b-sycl-routing-compatibility/run-v4-2026-10-12.json').read_bytes()
        self.manifest = json.loads((PACKET / 'local-9b-sycl-2026-10-12.manifest.json').read_text())

    def test_published_packet_reproduces_baseline_not_qualification(self):
        result = review(self.fixture, self.run, self.manifest)
        self.assertEqual((result['valid'], result['total'], result['exact_agreement']), (30, 30, 18))
        self.assertFalse(result['qualification_eligible'])
        self.assertFalse(result['deployment_authorized'])

    def test_scorer_drift(self):
        with self.assertRaises(ValueError):
            review(self.fixture, self.run, self.manifest, expected_scorer='0'*64)

    def test_fixture_drift(self):
        with self.assertRaises(ValueError):
            review(self.fixture + b' ', self.run, self.manifest)

    def test_run_drift(self):
        with self.assertRaises(ValueError):
            review(self.fixture, self.run + b' ', self.manifest)

    def test_tool_enable_rejected(self):
        self.manifest['tool_mode'] = 'enabled'
        with self.assertRaises(ValueError):
            review(self.fixture, self.run, self.manifest)

    def test_promotion_label_rejected(self):
        self.manifest['evidence_class'] = 'qualification'
        with self.assertRaises(ValueError):
            review(self.fixture, self.run, self.manifest)


if __name__ == '__main__':
    unittest.main()
