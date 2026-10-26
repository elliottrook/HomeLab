import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import stream_a_evaluation_guest_outcome as subject
from test_stream_a_evaluation_outcome_verifier import d4_ledger, m3_artifacts


class GuestOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, raw):
        path = self.root / name; path.write_bytes(raw); path.chmod(0o600)
        return path

    def test_d4_returns_only_content_free_projection(self):
        self.write("attempt-journal.jsonl", d4_ledger())
        with patch.object(subject, "D4_ROOT", self.root), \
                patch("pwd.getpwnam") as account:
            account.return_value.pw_uid = os.geteuid()
            value = subject.verify_local("d4-candidate-h")
        self.assertEqual(set(value), {"schema", "name", "journal_digest",
                                      "result_digest", "calls"})
        self.assertEqual(value["calls"], 12)

    def test_m3_reads_fixed_pair_and_rejects_weak_mode(self):
        run, journal = m3_artifacts()
        self.write("run.json", run); journal_path = self.write("attempt-journal.jsonl", journal)
        with patch.object(subject, "M3_ROOT", self.root), \
                patch.object(subject, "M3_UID", os.geteuid()):
            self.assertEqual(subject.verify_local("m3-nlu-calibration")["calls"], 60)
            journal_path.chmod(0o644)
            with self.assertRaises(subject.GuestOutcomeError):
                subject.verify_local("m3-nlu-calibration")

    def test_symlink_and_foreign_workload_fail(self):
        target = self.write("target", b"x")
        (self.root / "attempt-journal.jsonl").symlink_to(target)
        with patch.object(subject, "D4_ROOT", self.root), \
                patch("pwd.getpwnam") as account:
            account.return_value.pw_uid = os.geteuid()
            with self.assertRaises(subject.GuestOutcomeError):
                subject.verify_local("d4-candidate-h")
        with self.assertRaises(subject.GuestOutcomeError):
            subject.verify_local("other")

    def test_cli_is_inert_without_explicit_verification_gate(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(subject.main([]), 0)
        self.assertEqual(json.loads(output.getvalue()),
                         {"schema": subject.SCHEMA, "state": "disabled"})
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(subject.main(["--verify-authorized"]), 1)
        self.assertEqual(json.loads(output.getvalue())["state"], "no_go")


if __name__ == "__main__":
    unittest.main()
