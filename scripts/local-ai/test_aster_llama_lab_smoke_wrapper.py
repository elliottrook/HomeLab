import unittest

from aster_llama_lab_smoke_wrapper import (MODEL, MODEL_PATH, PORT, PROFILE,
    SERVER, server_command)


class LabSmokeWrapperTests(unittest.TestCase):
    def test_server_is_distinct_loopback_process(self):
        command = server_command("/run/lab/api-key")
        self.assertEqual(command[0], SERVER)
        self.assertIn("127.0.0.1", command)
        self.assertIn(str(PORT), command)
        self.assertIn(MODEL_PATH, command)
        self.assertEqual(PROFILE, "accepted-9b-direct-control-smoke-v1")
        self.assertEqual(MODEL, "aster-qwen3.5-9b")
        self.assertNotIn("aster-llama.service", command)


if __name__ == "__main__":
    unittest.main()
