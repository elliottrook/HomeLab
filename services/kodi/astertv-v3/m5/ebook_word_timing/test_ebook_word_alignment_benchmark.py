import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "ebook_word_alignment_benchmark", HERE / "ebook_word_alignment_benchmark.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BenchmarkContractTests(unittest.TestCase):
    def test_atomic_json_is_private_and_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            MODULE.atomic_json(path, {"passed": False})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(json.loads(path.read_text()), {"passed": False})
            with self.assertRaises(FileExistsError):
                MODULE.atomic_json(path, {})

    def test_hash_rejects_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_bytes(b"fixed")
            link = root / "link"
            link.symlink_to(target)
            with self.assertRaisesRegex(MODULE.BenchmarkError, "PINNED_FILE_CUSTODY"):
                MODULE.sha256(link)

    def test_hash_accepts_exact_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input"
            path.write_bytes(b"fixed")
            expected = hashlib.sha256(b"fixed").hexdigest()
            MODULE.require_hash(path, expected)

    def test_lease_identity_is_fixed(self):
        with mock.patch.object(MODULE, "require_runtime"), \
                mock.patch.object(MODULE, "load_inputs", return_value=("hello", 1.0)), \
                mock.patch.object(MODULE, "load_alignment"):
            with self.assertRaisesRegex(MODULE.BenchmarkError, "LEASE_IDENTITY"):
                MODULE.run("bad/lease", 1)

    def test_result_contract_contains_no_text_field(self):
        source = Path(MODULE.__file__).read_text(encoding="utf-8")
        self.assertNotIn('"transcript"', source)
        self.assertNotIn('"source_text"', source)
        self.assertIn('"text_exported": False', source)
        self.assertIn('"timestamps_inferred": False', source)


if __name__ == "__main__":
    unittest.main()
