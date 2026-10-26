import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UNIT = ROOT / "services/local-ai-lease/stream-a-evaluation-owner-heartbeat.service"


class OwnerHeartbeatUnitTests(unittest.TestCase):
    def test_owner_is_required_and_ordered_before_identity_condition(self):
        text = UNIT.read_text(encoding="utf-8")
        self.assertIn("Requires=stream-a-evaluation-owner.service", text)
        self.assertIn("After=local-fs.target stream-a-evaluation-owner.service", text)
        self.assertIn(
            "ConditionPathExists=/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json",
            text,
        )
        self.assertLess(text.index("After="), text.index("ConditionPathExists="))

    def test_heartbeat_remains_fixed_and_non_manual(self):
        text = UNIT.read_text(encoding="utf-8")
        for phrase in (
            "RefuseManualStart=yes",
            "ExecStart=/usr/local/sbin/stream-a-evaluation-owner-heartbeat --once --effect-authorized",
            "User=root",
            "NoNewPrivileges=yes",
            "ReadWritePaths=/var/lib/local-ai-lab/stream-a-evaluation",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
