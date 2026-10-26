import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F6-OWNER-HEARTBEAT-ORDERING-INACTIVE-UPGRADE-CARD-20261025.md"
UNIT = ROOT / "services/local-ai-lease/stream-a-evaluation-owner-heartbeat.service"


class OwnerHeartbeatOrderingUpgradeCardTests(unittest.TestCase):
    def test_card_pins_candidate_and_measured_prestate(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn(hashlib.sha256(UNIT.read_bytes()).hexdigest(), text)
        self.assertIn(
            "6c7777506df7aa2b58e62e3da7fb354859b6487e99441b4445c8a2a537df2ad5",
            text,
        )

    def test_card_is_one_file_inactive_and_rollback_bound(self):
        text = " ".join(CARD.read_text(encoding="utf-8").split())
        for phrase in (
            "Replace only the heartbeat service",
            "systemd-analyze verify",
            "daemon-reload",
            "F6 disabled/inactive",
            "must not enable or start the owner",
            "INSTALLATION NOT AUTHORIZED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
