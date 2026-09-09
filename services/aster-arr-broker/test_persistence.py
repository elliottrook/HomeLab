import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from persistence import MAX_AUDIT_BYTES, append_json_line, state_lock


class PersistenceTests(unittest.TestCase):
    def test_audit_append_is_private_and_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            append_json_line(path, {"result": "attempt_started"})
            append_json_line(path, {"result": "dismissed"})
            records = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(
                records,
                [{"result": "attempt_started"}, {"result": "dismissed"}],
            )
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_symlink_and_hardlinked_audit_paths_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("", encoding="utf-8")
            symlink = root / "audit-symlink"
            symlink.symlink_to(target)
            with self.assertRaises(OSError):
                append_json_line(symlink, {"result": "dismissed"})

            hardlink = root / "audit-hardlink"
            os.link(target, hardlink)
            with self.assertRaises(OSError):
                append_json_line(hardlink, {"result": "dismissed"})

    def test_oversized_audit_and_nonregular_lock_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit = root / "audit.jsonl"
            audit.write_bytes(b"x" * (MAX_AUDIT_BYTES + 1))
            with self.assertRaises(OSError):
                append_json_line(audit, {"result": "dismissed"})

            lock = root / "broker.lock"
            lock.mkdir()
            with self.assertRaises(OSError):
                with state_lock(lock):
                    pass

    def test_short_writes_are_completed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audit.jsonl"
            real_write = os.write

            def short_write(descriptor, payload):
                return real_write(descriptor, payload[: max(1, len(payload) // 2)])

            with patch("persistence.os.write", side_effect=short_write):
                append_json_line(path, {"result": "dismissed"})
            self.assertEqual(json.loads(path.read_text()), {"result": "dismissed"})


if __name__ == "__main__":
    unittest.main()
