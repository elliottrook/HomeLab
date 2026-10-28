import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import lab_hours_exact_cycle_runner_20261029 as runner


class ExactCycleRunnerTests(unittest.TestCase):
    def test_commands_are_fixed_to_release_candidate(self):
        owner = runner.owner_command(100)
        guardian = runner.guardian_command(100)
        self.assertIn("--effect-authorized", owner)
        self.assertIn("--news-overlap-authorized", owner)
        self.assertEqual(owner[owner.index("--cycle") + 1], "2026_10_29")
        self.assertEqual(guardian[guardian.index("--rescue-at") + 1], "1900")
        self.assertEqual(guardian[guardian.index("--hard-deadline") + 1], "2800")

    def test_failure_record_is_content_free_and_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / "attempt"
            with patch.object(runner, "EVIDENCE", evidence), \
                 patch.object(runner, "require_static", side_effect=runner.NightRunError("detail")), \
                 patch.object(runner.time, "time", return_value=100):
                self.assertEqual(runner.main(), 1)
            value = json.loads((evidence / "terminal.json").read_text())
            self.assertEqual(value["state"], "no_go")
            self.assertEqual(value["first_failure_phase"], "static-preflight")
            self.assertNotIn("detail", json.dumps(value))


if __name__ == "__main__":
    unittest.main()
