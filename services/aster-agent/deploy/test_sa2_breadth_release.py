import json
import tempfile
import unittest
from pathlib import Path

from validate_sa2_breadth_release import MANIFEST, ROOT, validate


class BreadthReleaseTests(unittest.TestCase):
    def test_release_validates(self):
        result = validate()
        self.assertEqual(result["mac_files"], 4)
        self.assertEqual(result["lxc_files"], 9)
        self.assertFalse(result["model_change"])
        self.assertFalse(result["repair_authority"])

    def test_manifest_rejects_runtime_expansion(self):
        value = json.loads(MANIFEST.read_text())
        value["runtime"]["automatic_routing"] = True
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "runtime boundary"):
                validate(ROOT, path)

    def test_manifest_rejects_source_drift(self):
        value = json.loads(MANIFEST.read_text())
        value["lxc_files"][0]["after_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "candidate source hash"):
                validate(ROOT, path)


if __name__ == "__main__":
    unittest.main()
