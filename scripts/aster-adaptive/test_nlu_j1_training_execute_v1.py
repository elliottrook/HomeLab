import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import nlu_j1_training_execute_v1 as execute


class J1TrainingExecuteTests(unittest.TestCase):
    def test_audit_rejects_network_and_allows_unrelated_events(self):
        with self.assertRaises(RuntimeError):
            execute._audit("socket.connect", ())
        execute._audit("open", ())

    def test_exclusive_writer_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "value"
            execute._write_exclusive(path, b"one")
            self.assertEqual(b"one", path.read_bytes())
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            with self.assertRaises(FileExistsError):
                execute._write_exclusive(path, b"two")

    def test_worker_requires_empty_existing_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "missing"
            with self.assertRaises(ValueError):
                execute.worker(Path("x"), Path("y"), Path("z"), output)
            output.mkdir(); (output / "occupied").write_text("x")
            with self.assertRaises(ValueError):
                execute.worker(Path("x"), Path("y"), Path("z"), output)

    def test_execution_fails_closed_on_worker_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"; corpus.write_bytes(b"c")
            release = root / "release"; release.write_bytes(b"r")
            private = root / "private"; private.mkdir()
            for name in (*execute.RECEIPT_NAMES, "private-review-result"):
                (private / f"{name}.json").write_bytes(b"{}")
            output = root / "retained"
            completed = type("Completed", (), {"returncode": 0, "stdout": b"unexpected", "stderr": b""})()
            with patch.object(execute.subprocess, "run", return_value=completed):
                with self.assertRaises(RuntimeError):
                    execute.execute(corpus, release, private, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
