import unittest
from unittest.mock import patch

from application_b60_drill_entrypoint import main


class ApplicationDrillEntrypointTests(unittest.TestCase):
    def test_plan_is_effect_free_and_lists_bounded_phases(self):
        with patch("application_b60_drill_entrypoint.os.geteuid", return_value=1000):
            self.assertEqual(main(["--phase", "plan"]), 0)

    def test_effectful_phases_require_root(self):
        with patch("application_b60_drill_entrypoint.os.geteuid", return_value=1000):
            with self.assertRaisesRegex(SystemExit, "requires root"):
                main(["--phase", "acquire", "--prelease", "/tmp/prelease.json"])

    def test_effectful_phases_have_no_arbitrary_command_argument(self):
        with self.assertRaises(SystemExit):
            main(["--help", "--command", "sh"])

    def test_lease_state_directory_is_fixed(self):
        with self.assertRaisesRegex(SystemExit, "state directory is fixed"):
            main(["--phase", "plan", "--state-dir", "/tmp/other"])


if __name__ == "__main__":
    unittest.main()
