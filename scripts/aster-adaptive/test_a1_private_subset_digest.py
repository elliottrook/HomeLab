import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE = Path(__file__).with_name("a1_private_subset_digest.py")
SPEC = importlib.util.spec_from_file_location("a1_private_subset_digest", MODULE)
assert SPEC and SPEC.loader
digest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(digest)


class PrivateSubsetDigestTests(unittest.TestCase):
    def test_repeatable_content_free_result_and_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "nested").mkdir()
            (root / "nested" / "fictional.txt").write_text("fictional")
            first = digest.scan(root)
            self.assertEqual(first["entry_count"], 1)
            self.assertEqual(first["total_size"], 9)
            self.assertNotIn("fictional", str(first))
            expected_row = [("nested/fictional.txt", 9, hashlib.sha256(b"fictional").hexdigest())]
            expected_manifest = hashlib.sha256(
                json.dumps(expected_row, separators=(",", ":"), ensure_ascii=True).encode()
            ).hexdigest()
            self.assertEqual(first["manifest_sha256"], expected_manifest)
            self.assertEqual(first["manifest_sha256"], digest.scan(root)["manifest_sha256"])
            (root / "nested" / "fictional.txt").write_text("different")
            self.assertNotEqual(first["manifest_sha256"], digest.scan(root)["manifest_sha256"])

    def test_symlink_and_extra_files_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one").write_text("one")
            (root / "link").symlink_to(root / "one")
            with self.assertRaises(digest.ScanError):
                digest.scan(root)
            (root / "link").unlink()
            (root / "two").write_text("two")
            with self.assertRaises(digest.ScanError):
                digest.scan(root, max_files=1)

    def test_empty_and_oversize_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(digest.ScanError):
                digest.scan(root)
            (root / "one").write_text("large")
            with self.assertRaises(digest.ScanError):
                digest.scan(root, max_bytes=2)

    def test_file_replaced_by_symlink_before_open_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "one"
            target.write_text("fictional")
            outside = root.parent / (root.name + "-outside")
            outside.write_text("do not read")
            real_open = digest.os.open

            def swap_then_open(path, flags, *args, **kwargs):
                if path == "one":
                    target.unlink()
                    target.symlink_to(outside)
                return real_open(path, flags, *args, **kwargs)

            try:
                with patch.object(digest.os, "open", side_effect=swap_then_open):
                    with self.assertRaises(OSError):
                        digest.scan(root)
            finally:
                outside.unlink()

    def test_directory_replaced_by_symlink_before_open_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "nested"
            target.mkdir()
            (target / "one").write_text("fictional")
            outside = root.parent / (root.name + "-outside")
            outside.mkdir()
            real_open = digest.os.open

            def swap_then_open(path, flags, *args, **kwargs):
                if path == "nested":
                    target.rename(root / "moved")
                    target.symlink_to(outside, target_is_directory=True)
                return real_open(path, flags, *args, **kwargs)

            try:
                with patch.object(digest.os, "open", side_effect=swap_then_open):
                    with self.assertRaises(OSError):
                        digest.scan(root)
            finally:
                outside.rmdir()


if __name__ == "__main__":
    unittest.main()
