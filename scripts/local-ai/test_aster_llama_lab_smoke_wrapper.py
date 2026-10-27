import unittest
from pathlib import Path

from aster_llama_lab_smoke_wrapper import (MODEL, MODEL_PATH, PORT, PROFILE,
    SERVER, _stop_scope, production_is_masked, scope_unit, server_command)


class LabSmokeWrapperTests(unittest.TestCase):
    def test_production_mask_uses_runtime_symlink(self):
        import subprocess
        def runner(command, **kwargs):
            if command[0] == "readlink":
                return subprocess.CompletedProcess(command, 0, "/dev/null\n", "")
            return subprocess.CompletedProcess(command, 3, "inactive\n", "")
        self.assertTrue(production_is_masked(runner))

    def test_server_is_distinct_loopback_process(self):
        command = server_command("/run/lab/api-key", lease_id="lease-1", generation=2)
        self.assertEqual(command[0], "/usr/bin/systemd-run")
        self.assertIn("--scope", command)
        self.assertIn(f"--unit={scope_unit('lease-1', 2)}", command)
        self.assertIn(SERVER, command)
        self.assertIn("127.0.0.1", command)
        self.assertIn(str(PORT), command)
        self.assertIn(MODEL_PATH, command)
        self.assertEqual(command[command.index("--alias") + 1], MODEL)
        self.assertEqual(PROFILE, "accepted-9b-direct-control-smoke-v1")
        self.assertEqual(MODEL, "aster-qwen3.5-9b")
        self.assertNotIn("aster-llama.service", command)

    def test_cli_contract_names_lease_identity(self):
        import subprocess
        source = Path("scripts/local-ai/aster_llama_lab_smoke_wrapper.py").read_text(encoding="utf-8")
        self.assertIn('add_argument("--lease-id", required=True)', source)
        self.assertIn('add_argument("--generation", required=True', source)
        self.assertIn('add_argument("--profile", required=True)', source)
        self.assertIn("_wait_ready", source)

    def test_already_gone_collect_scope_is_harmless(self):
        import subprocess
        def gone(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 5, "", "Unit a.scope not loaded.")
        result = _stop_scope("a.scope", runner=gone)
        self.assertEqual(result.returncode, 0)

    def test_unexpected_scope_stop_failure_remains_failure(self):
        import subprocess
        def failed(*args, **kwargs):
            return subprocess.CompletedProcess(args[0], 5, "", "permission denied")
        result = _stop_scope("a.scope", runner=failed)
        self.assertEqual(result.returncode, 5)


if __name__ == "__main__":
    unittest.main()
