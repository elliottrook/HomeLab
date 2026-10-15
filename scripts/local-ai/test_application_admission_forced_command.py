import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class ApplicationForcedCommandTests(unittest.TestCase):
    def test_forced_command_is_fixed_and_rejects_shell_shape(self):
        source = (ROOT / "services/local-ai-lease/application-admission-forced-command").read_text()
        self.assertIn("SSH_ORIGINAL_COMMAND", source)
        self.assertIn("application_admission_cli.py --profile", source)
        self.assertIn("exit 126", source)
        self.assertNotIn("$@", source)


if __name__ == "__main__":
    unittest.main()
