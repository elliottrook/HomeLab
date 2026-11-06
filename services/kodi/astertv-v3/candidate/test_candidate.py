import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


path = Path(__file__).with_name("build_candidate.py")
spec = importlib.util.spec_from_file_location("build_candidate", path)
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


class CandidateTests(unittest.TestCase):
    def test_path_validation_rejects_escape_and_absolute_paths(self):
        for value in ("../escape", "/absolute", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                candidate.safe_relative(value)

    def test_secret_scan_rejects_credentials_and_private_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fixture.py"
            path.write_text("api_key = 'not-a-real-key'\n")
            with self.assertRaises(ValueError):
                candidate.scan([path])
            path.write_text("-----BEGIN TEST PRIVATE KEY-----\n")
            with self.assertRaises(ValueError):
                candidate.scan([path])

    def test_reproducible_archive_validates_every_declared_member(self):
        with tempfile.TemporaryDirectory(dir=candidate.ROOT) as temporary:
            path = Path(temporary) / "fixture.txt"
            path.write_text("fixture")
            row = {"path": path.relative_to(candidate.ROOT).as_posix(),
                   "bytes": path.stat().st_size, "sha256": candidate.sha256_file(path)}
            manifest = (json.dumps({"inputs": [row]}) + "\n").encode()
            first = candidate.tar_bytes([path], manifest, [])
            second = candidate.tar_bytes([path], manifest, [])
            self.assertEqual(first, second)
            self.assertEqual(candidate.validate_archive(first)["inputs"], [row])

    def test_fixture_schema_is_synthetic_and_maps_f1_to_f12(self):
        data = json.loads(Path(__file__).with_name("fixture-schema.json").read_text())
        self.assertEqual(data["credential_policy"], "synthetic-only")
        keys = {page["key"] for page in data["pages"]}
        self.assertTrue({"F1", "F2", "F3", "F4", "F5", "F6", "F8", "F9", "F10", "F11", "F12"} <= keys)

    def test_page_candidate_inventory_includes_m9_screensaver(self):
        paths = {path.relative_to(candidate.V3).as_posix()
                 for path in candidate.source_files()}
        self.assertIn("screensaver/addon.xml", paths)
        self.assertIn("screensaver/default.py", paths)
        self.assertIn("screensaver/policy.py", paths)
        self.assertIn("screensaver/service.py", paths)
        self.assertIn("screensaver/test_screensaver.py", paths)


if __name__ == "__main__":
    unittest.main()
