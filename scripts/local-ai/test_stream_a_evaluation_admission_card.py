import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/STREAM-A-EVALUATION-ADMISSION-CANDIDATE-H-INACTIVE-INSTALL-CARD-20261025.md"


class AdmissionInstallCardTests(unittest.TestCase):
    def test_source_hashes_match_and_live_effects_are_excluded(self):
        text = CARD.read_text()
        prose = " ".join(text.split())
        for relative in (
            "scripts/local-ai/stream_a_evaluation_admission.py",
            "scripts/local-ai/evaluation_lease.py",
            "scripts/local-ai/evaluation_lease_adapter.py",
            "scripts/local-ai/evaluation_lease_entrypoint.py",
        ):
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertRegex(text, re.escape(relative) + r"[^\n]+" + digest)
        for phrase in (
            "does not create F4 or F5 evidence",
            "two recovery timers still disabled/inactive",
            "first workload is now `d4-candidate-h`",
        ):
            self.assertIn(phrase, prose)


if __name__ == "__main__":
    unittest.main()
