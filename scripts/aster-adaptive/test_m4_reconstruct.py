import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from m4_reconstruct import load_manifest


def sha(data=b"x"):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def manifest():
    return {
        "schema": "aster-m4-reconstruction-manifest.v1",
        "data_class": "synthetic",
        "evidence_path": "evidence.json",
        "expected_head": sha(b"head"),
        "files": {"evidence.json": sha()},
        "expected": {"event_count": 164,
                     "measurement_authenticity": "not-established",
                     "review_approval": "not-granted"},
        "runtime": {"python": "3.14.0", "pydantic": "2.14.1"},
        "authority": "not-granted",
    }


class M4ReconstructTests(unittest.TestCase):
    def write(self, value):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        path = Path(root.name) / "manifest.json"
        path.write_text(json.dumps(value))
        return path

    def test_accepts_bounded_manifest(self):
        self.assertEqual("synthetic", load_manifest(self.write(manifest()))["data_class"])

    def test_rejects_traversal_unpinned_export_and_authority(self):
        changes = [
            {"evidence_path": "../private.json"},
            {"files": {"other.json": sha()}},
            {"authority": "granted"},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(ValueError):
                load_manifest(self.write(manifest() | change))

    def test_rejects_duplicate_json_keys(self):
        path = self.write(manifest())
        raw = path.read_text()
        path.write_text(raw[:-1] + ',"authority":"not-granted"}')
        with self.assertRaisesRegex(ValueError, "duplicate"):
            load_manifest(path)


if __name__ == "__main__":
    unittest.main()
