import hashlib
import os
import tempfile
import unittest
from pathlib import Path

from a1_key_file import append_key, remove_key_hash


class A1KeyFileTests(unittest.TestCase):
    def test_append_and_hash_bound_remove_preserve_production_key(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "keys"
            checkpoint = root / "checkpoint"
            path.write_bytes(b"production-key\n")
            os.chmod(path, 0o640)
            test_key = b"t" * 40
            digest = append_key(path, checkpoint, test_key, uid=os.getuid(), gid=os.getgid())
            self.assertEqual(digest, hashlib.sha256(test_key).hexdigest())
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(checkpoint.read_bytes(), b"production-key\n")
            remove_key_hash(path, checkpoint, digest, uid=os.getuid(), gid=os.getgid())
            self.assertEqual(path.read_bytes(), b"production-key\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)
            self.assertEqual(checkpoint.read_bytes(), b"production-key\n")
            remove_key_hash(path, checkpoint, digest, uid=os.getuid(), gid=os.getgid())

    def test_remove_refuses_unknown_or_ambiguous_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "keys"
            checkpoint = root / "checkpoint"
            path.write_bytes(b"one\ntwo\n")
            with self.assertRaises(ValueError):
                remove_key_hash(path, checkpoint, "0" * 64, uid=os.getuid(), gid=os.getgid())

    def test_append_refuses_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "keys"
            path.write_bytes(b"t" * 40 + b"\n")
            with self.assertRaises(ValueError):
                append_key(path, root / "checkpoint", b"t" * 40, uid=os.getuid(), gid=os.getgid())

    def test_existing_checkpoint_cannot_be_redefined(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "keys"
            checkpoint = root / "checkpoint"
            path.write_bytes(b"production-key")
            checkpoint.write_bytes(b"wrong-original")
            with self.assertRaisesRegex(ValueError, "checkpoint"):
                append_key(path, checkpoint, b"t" * 40, uid=os.getuid(), gid=os.getgid())

    def test_final_line_without_newline_is_checked_exactly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "keys"
            checkpoint = root / "checkpoint"
            path.write_bytes(b"production-key")
            digest = append_key(path, checkpoint, b"t" * 40, uid=os.getuid(), gid=os.getgid())
            remove_key_hash(path, checkpoint, digest, uid=os.getuid(), gid=os.getgid())
            self.assertEqual(path.read_bytes(), b"production-key")


if __name__ == "__main__":
    unittest.main()
