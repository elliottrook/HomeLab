import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("apply_fixed_doctor_broker_reconciliation.sh")


class BrokerApplyBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.text = SCRIPT.read_text()

    def test_exact_sources_and_registered_health_identity_are_pinned(self):
        self.assertIn("expected_admin=00216b27", self.text)
        self.assertIn("candidate_admin=e90acd24", self.text)
        self.assertIn("expected_service=05a55524", self.text)
        self.assertIn("candidate_service=c6217f49", self.text)
        self.assertGreaterEqual(self.text.count("runuser -u hlabagent"), 2)
        self.assertNotIn("runuser -u aster --", self.text)

    def test_rollback_restores_database_custody_and_only_broker_restarts(self):
        self.assertIn(
            'install -o hlabroker -g hlabroker -m 0600 "$checkpoint/broker.db" "$database"',
            self.text,
        )
        self.assertNotIn("systemctl restart aster-agent", self.text)
        self.assertEqual(2, self.text.count("systemctl restart homelab-broker.service"))

    def test_effect_boundary_excludes_activation_and_enrollment(self):
        self.assertNotIn("broker_admin.py --database", self.text)
        self.assertNotIn("systemctl enable", self.text)
        self.assertNotIn("systemctl start aster-fixed", self.text)
        self.assertIn("fixed_counts=0,0,0,0,0", self.text)


if __name__ == "__main__":
    unittest.main()
