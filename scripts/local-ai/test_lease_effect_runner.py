import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from lease_controller_candidate import command_for
from lease_effect_runner import EffectError, EffectRunner


class EffectRunnerTests(unittest.TestCase):
    def test_runs_only_exact_allowlisted_commands(self):
        runner = EffectRunner()
        with patch("lease_effect_runner.subprocess.run", return_value=subprocess.CompletedProcess((), 0)) as run:
            runner.run(command_for("110", "aster-llama.service", "stop"))
        run.assert_called_once()
        self.assertEqual(run.call_args.kwargs["check"], False)
        self.assertEqual(run.call_args.kwargs["timeout"], 15.0)

    def test_rejects_shell_and_unknown_unit(self):
        runner = EffectRunner()
        with self.assertRaisesRegex(EffectError, "boundary"):
            runner.run(("sh", "-c", "pct exec 110 -- systemctl stop aster-llama.service"))
        with self.assertRaisesRegex(EffectError, "allowlist"):
            runner.run(command_for("110", "aster-llama.service", "stop")[:-1] + ("sshd.service",))

    def test_timeout_and_nonzero_fail_closed(self):
        runner = EffectRunner(timeout=2.0)
        with patch("lease_effect_runner.subprocess.run", side_effect=subprocess.TimeoutExpired("pct", 2.0)):
            with self.assertRaisesRegex(EffectError, "did not complete"):
                runner.run(command_for("110", "aster-llama.service", "start"))
        with patch("lease_effect_runner.subprocess.run", return_value=subprocess.CompletedProcess((), 1)):
            with self.assertRaisesRegex(EffectError, "returned failure"):
                runner.run(command_for("110", "aster-llama.service", "start"))

    def test_unit_and_timer_remain_disabled_candidate(self):
        root = Path(__file__).parents[2] / "services/local-ai-lease"
        unit = (root / "local-ai-lease-watchdog.service").read_text()
        timer = (root / "local-ai-lease-watchdog.timer").read_text()
        self.assertIn("RefuseManualStart=yes", unit)
        self.assertIn("ConditionPathExists=", unit)
        self.assertIn("disabled candidate", timer)


if __name__ == "__main__":
    unittest.main()
