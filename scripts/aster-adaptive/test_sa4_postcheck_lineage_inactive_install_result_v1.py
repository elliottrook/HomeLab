import unittest
from pathlib import Path

import sa4_postcheck_lineage_inactive_install_result_v1 as source


ROOT = Path(__file__).parents[2]
RESULT = ROOT / ("docs/projects/AI Projects/evidence/"
                 "SA4-postcheck-lineage-inactive-install-result-2026-11-06.json")


class Tests(unittest.TestCase):
    def test_result_is_exact_and_inert(self):
        value = source.validate(RESULT.read_bytes())
        self.assertTrue(value["inactive"])
        self.assertTrue(value["v2_postchecks_pass"])
        self.assertFalse(value["repair_authorized"])


if __name__ == "__main__":
    unittest.main()
