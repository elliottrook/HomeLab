import json
from pathlib import Path
import unittest

import sa4_distinct_registry_fix_inactive_install_result_v1 as source


ROOT = Path(__file__).parents[2]
RESULT = ROOT / (
    "docs/projects/AI Projects/evidence/"
    "SA4-distinct-registry-fix-inactive-install-result-2026-11-06.json")


class Tests(unittest.TestCase):
    def test_retained_result_is_exact_and_inactive(self):
        value = source.validate(RESULT.read_bytes())
        self.assertTrue(value["inactive"])
        self.assertFalse(value["repair_authorized"])

    def test_changed_effect_boundary_rejected(self):
        value = json.loads(RESULT.read_bytes())
        value["repair_authorized"] = True
        with self.assertRaises(ValueError):
            source.validate(json.dumps(value).encode())

    def test_changed_hash_rejected(self):
        value = json.loads(RESULT.read_bytes())
        value["rows"][0]["after_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            source.validate(json.dumps(value).encode())


if __name__ == "__main__":
    unittest.main()

