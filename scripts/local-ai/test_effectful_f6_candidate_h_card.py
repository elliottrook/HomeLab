import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/STREAM-A-EVALUATION-LEASE-EFFECTFUL-F6-CANDIDATE-H-CARD-20261025.md"


class EffectfulF6CandidateHCardTests(unittest.TestCase):
    def test_card_pins_current_controller_sources_and_wrappers(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/evaluation_lease.py",
            "scripts/local-ai/evaluation_lease_adapter.py",
            "scripts/local-ai/evaluation_lease_entrypoint.py",
            "scripts/local-ai/stream_a_evaluation_admission.py",
            "scripts/local-ai/evaluation_lease_watchdog.py",
            "scripts/local-ai/host_exclusion.py",
            "scripts/local-ai/stream_a_evaluation_watchdog.py",
            "scripts/local-ai/stream_a_evaluation_owner.py",
            "scripts/local-ai/stream_a_evaluation_owner_heartbeat.py",
            "scripts/local-ai/stream_a_evaluation_restore_observer.py",
            "services/local-ai-lease/stream-a-evaluation-lease",
            "services/local-ai-lease/stream-a-evaluation-owner",
            "services/local-ai-lease/stream-a-evaluation-owner-heartbeat",
            "services/local-ai-lease/stream-a-evaluation-watchdog",
            "services/local-ai-lease/stream-a-evaluation-restore-observe",
        ):
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertIn(digest, text, relative)

    def test_card_fixes_boundaries_and_real_workloads(self):
        text = " ".join(CARD.read_text(encoding="utf-8").split())
        for phrase in (
            "A later source revision must provide that orchestrator",
            "systemctl enable --now stream-a-evaluation-owner-heartbeat.timer",
            "systemctl enable --now stream-a-evaluation-watchdog.timer",
            "RefuseManualStart=yes",
            "pct exec 104 -- systemctl start aster-d4-candidate-h.service",
            "nlu_calibration_runner.py --source cases.json",
            "--key-file /etc/aster-llama-api-keys",
            "The first command may run once only",
            "Uncertain cleanup retains state and locks for reconciliation",
        ):
            self.assertIn(phrase, text)

    def test_card_remains_non_authorizing(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("SOURCE-ONLY FUTURE RUN CARD; HOLD", text)
        self.assertIn("It is not authority", text)


if __name__ == "__main__":
    unittest.main()
