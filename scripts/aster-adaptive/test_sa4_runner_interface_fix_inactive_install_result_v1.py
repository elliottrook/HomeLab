import unittest
from pathlib import Path

import sa4_runner_interface_fix_inactive_install_result_v1 as source


ROOT = Path(__file__).parents[2]
RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-runner-interface-fix-inactive-install-result-2026-11-06.json")


class Tests(unittest.TestCase):
    def test_retained_result_is_exact_and_inert(self):
        value = source.validate(RESULT.read_bytes())
        self.assertTrue(value["inactive"])
        self.assertFalse(value["repair_authorized"])
        self.assertTrue(value["retained_failed_attempt_exact"])


if __name__ == "__main__":
    unittest.main()
