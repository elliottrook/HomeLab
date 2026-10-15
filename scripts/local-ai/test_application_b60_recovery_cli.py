import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


class ApplicationRecoveryCliTests(unittest.TestCase):
    def test_dry_run_is_effect_free_and_lists_only_fixed_commands(self):
        root = Path(__file__).parents[2]
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "application-b60.json"
            state.write_text(json.dumps({"mode": "application-b60-exclusive-v1", "lease_id": "lease-1", "generation": 2, "armed": True, "start_deadline_epoch": 150, "restore_deadline_epoch": 200}))
            result = subprocess.run(["/usr/bin/python3", str(root / "scripts/local-ai/application_b60_lease_recovery.py"), "--once", "--state", str(state), "--dry-run"], capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0)
            output = json.loads(result.stdout)
            self.assertEqual(output["state"], "dry-run")
            self.assertIn("aster-a1-test.service", " ".join(" ".join(command) for command in output["commands"]))
            self.assertEqual(state.read_text().count("lease-1"), 1)

    def test_effectful_mode_requires_explicit_authority(self):
        root = Path(__file__).parents[2]
        with tempfile.TemporaryDirectory() as temp:
            state = Path(temp) / "application-b60.json"
            state.write_text(json.dumps({"mode": "application-b60-exclusive-v1", "lease_id": "lease-1", "generation": 2, "armed": True, "start_deadline_epoch": 150, "restore_deadline_epoch": 200}))
            result = subprocess.run(["/usr/bin/python3", str(root / "scripts/local-ai/application_b60_lease_recovery.py"), "--once", "--state", str(state)], capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertRegex(result.stderr, "effect authority|must run as root")

    def test_source_drift_is_not_a_pre_recovery_blocker(self):
        # The CLI records candidate-source drift in the terminal receipt after
        # production recovery; it must not gate watchdog restoration.
        source = Path(__file__).parents[2] / "scripts/local-ai/application_b60_lease_recovery.py"
        self.assertIn("source_checks()", source.read_text())
        self.assertIn("retain_state=True", source.read_text())

    def test_waiting_tick_uses_current_time_not_deadline_substitution(self):
        source = Path(__file__).parents[2] / "scripts/local-ai/application_b60_lease_recovery.py"
        text = source.read_text()
        self.assertIn("now_epoch < state[\"restore_deadline_epoch\"]", text)
        self.assertIn("now_epoch=now_epoch", text)

    def test_recovery_cli_does_not_construct_production_key_argv(self):
        text = (Path(__file__).parents[2] / "scripts/local-ai/application_b60_lease_recovery.py").read_text()
        self.assertNotIn("cat /etc/aster-llama-api-keys", text)
        self.assertIn("aster-llama-production-auth-probe", text)
