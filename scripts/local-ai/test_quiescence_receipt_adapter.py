import unittest

from admission_gate import AdmissionEvidenceError, EXPECTED_CONSUMERS
from quiescence_receipt_adapter import ConsumerSnapshot, compose_quiescence_receipt


class QuiescenceReceiptAdapterTests(unittest.TestCase):
    def sample(self, **changes):
        values = {
            "observed_minute": 1057,
            "observed_monotonic": 100,
            "active_states": ("inactive",) * len(EXPECTED_CONSUMERS),
            "active_enter_monotonic": (10, 20, 30, 40),
            "news_timer_active": False,
            "no_new_starts_marker": "generation-1",
        }
        values.update(changes)
        return ConsumerSnapshot(**values)

    def test_requires_stable_two_sample_quiescence(self):
        result = compose_quiescence_receipt(self.sample(), self.sample(observed_minute=1058, observed_monotonic=110))
        self.assertTrue(result.source_observed)
        self.assertEqual(result.consumers, EXPECTED_CONSUMERS)

    def test_rejects_active_consumer_or_news(self):
        with self.assertRaisesRegex(AdmissionEvidenceError, "consumer"):
            compose_quiescence_receipt(self.sample(active_states=("active", "inactive", "inactive", "inactive")), self.sample(observed_minute=1058, observed_monotonic=110))
        with self.assertRaisesRegex(AdmissionEvidenceError, "News"):
            compose_quiescence_receipt(self.sample(), self.sample(observed_minute=1058, observed_monotonic=110, news_timer_active=True))


if __name__ == "__main__":
    unittest.main()
