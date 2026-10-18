import unittest
from pathlib import Path

from aster_llama_lab_smoke_wrapper import (MODEL, MODEL_PATH, PORT, PROFILE,
    SERVER, server_command)


class LabSmokeWrapperTests(unittest.TestCase):
    def test_server_is_distinct_loopback_process(self):
        command = server_command("/run/lab/api-key")
        self.assertEqual(command[0], "/usr/sbin/runuser")
        self.assertIn(SERVER, command)
        self.assertIn("127.0.0.1", command)
        self.assertIn(str(PORT), command)
        self.assertIn(MODEL_PATH, command)
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


if __name__ == "__main__":
    unittest.main()
