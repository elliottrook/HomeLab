import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class Sa3ManifestTests(unittest.TestCase):
    def test_manifest_is_exact_development_subset(self):
        manifest = json.loads((ROOT / "sysadmin-sa3-development-manifest-v1.json").read_text())
        source = json.loads((ROOT / manifest["source_suite"]).read_text())
        source_ids = {case["id"] for case in source["cases"]}
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["role"], "development_regression_only")
        self.assertEqual(len(manifest["case_ids"]), 12)
        self.assertEqual(len(set(manifest["case_ids"])), 12)
        self.assertTrue(set(manifest["case_ids"]).issubset(source_ids))
        self.assertTrue(any("not an independently reviewed holdout" in item.lower() for item in manifest["limitations"]))


if __name__ == "__main__":
    unittest.main()
