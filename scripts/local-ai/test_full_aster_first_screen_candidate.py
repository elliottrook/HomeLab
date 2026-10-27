import unittest

import full_aster_first_screen_candidate as candidate


class CandidateCommandTests(unittest.TestCase):
    def test_start_is_one_fixed_transient_reasoning_on_unit(self):
        command = candidate.start_command()
        self.assertEqual(command[:5], ("pct", "exec", "110", "--", "/usr/bin/systemd-run"))
        self.assertIn("--collect", command)
        self.assertIn("--property=Restart=no", command)
        self.assertIn("--property=User=ollama", command)
        self.assertIn("--setenv=ONEAPI_DEVICE_SELECTOR=level_zero:gpu", command)
        self.assertEqual(command.count("--reasoning"), 1)
        self.assertEqual(command[command.index("--reasoning") + 1], "on")
        self.assertNotIn("--draft-model", command)
        self.assertEqual(command[command.index("-np") + 1], "1")
        self.assertEqual(command[command.index("-c") + 1], "8192")
        self.assertEqual(command[command.index("-m") + 1], candidate.MODEL)

    def test_stop_reset_and_baseline_commands_are_fixed_to_lxc110(self):
        self.assertEqual(candidate.stop_command(),
            ("pct", "exec", "110", "--", "systemctl", "stop", candidate.UNIT))
        self.assertEqual(candidate.reset_failed_command(),
            ("pct", "exec", "110", "--", "systemctl", "reset-failed", candidate.UNIT))
        self.assertEqual(candidate.baseline_stop_command()[-2:], ("stop", "aster-llama.service"))
        self.assertEqual(candidate.baseline_start_command()[-2:], ("start", "aster-llama.service"))

    def test_endpoint_api_key_file_and_runtime_are_not_selectable(self):
        command = candidate.start_command()
        self.assertEqual(command[command.index("--host") + 1], "192.168.70.12")
        self.assertEqual(command[command.index("--port") + 1], "11435")
        self.assertEqual(command[command.index("--api-key-file") + 1],
                         "/etc/aster-llama-api-keys")
        self.assertEqual(command[command.index(candidate.BINARY)], candidate.BINARY)


if __name__ == "__main__":
    unittest.main()
