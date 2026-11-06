import unittest
from pathlib import Path

import sa4_fresh_path_runner_inactive_install_result_v1 as source


ROOT = Path(__file__).parents[2]
RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-fresh-path-runner-inactive-install-result-2026-11-06.json")


class Tests(unittest.TestCase):
    def test_retained_result_is_exact_and_inert(self):
        value = source.validate(RESULT.read_bytes())
        self.assertTrue(value["inactive"])
        self.assertTrue(value["fresh_v3_state_absent"])
        self.assertFalse(value["repair_authorized"])


if __name__ == "__main__":
    unittest.main()
