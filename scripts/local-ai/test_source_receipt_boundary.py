import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from admission_gate import EXPECTED_BACKUP_SOURCE, EXPECTED_CONSUMERS, AdmissionEvidence
from source_receipt_boundary import _validate_payload, _write_envelope, produce_candidate_receipt, read_receipt


class SourceReceiptBoundaryTests(unittest.TestCase):
    def evidence(self):
        return AdmissionEvidence(EXPECTED_BACKUP_SOURCE, "receipt", 220, True, EXPECTED_CONSUMERS, True, True)

    @unittest.skipUnless(os.geteuid() == 0, "requires root-owned custody test")
    def test_root_owned_envelope_binds_lease(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            _write_envelope(path, self.evidence(), lease_id="lab-1", generation=2, captured_epoch=100)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(read_receipt(path, lease_id="lab-1", generation=2, now_minute=221, window_end_minute=255, now_epoch=101), "receipt")
            with self.assertRaisesRegex(ValueError, "current lease"):
                read_receipt(path, lease_id="lab-1", generation=3, now_minute=221, window_end_minute=255, now_epoch=101)

    def test_untrusted_marker_does_not_authorize(self):
        payload = self.valid_payload()
        payload["boundary"] = "fake"
        with self.assertRaisesRegex(ValueError, "current lease"):
            self.validate(payload)

    def valid_payload(self):
        evidence = self.evidence()
        return {"boundary": "aster-source-receipt-boundary-v1", "lease_id": "lab-1",
                "generation": 2, "captured_epoch": 100,
                "evidence": {"source": evidence.source,
                             "backup_receipt": evidence.backup_receipt,
                             "backup_completed_minute": evidence.backup_completed_minute,
                             "backup_verified": evidence.backup_verified,
                             "consumers_quiesced": list(evidence.consumers_quiesced),
                             "news_quiesced": evidence.news_quiesced,
                             "source_observed": evidence.source_observed}}

    def validate(self, payload):
        return _validate_payload(payload, lease_id="lab-1", generation=2,
                                 now_minute=221, window_end_minute=255,
                                 now_epoch=101, max_age_seconds=900)

    def test_malformed_receipt_types_and_fields_fail_closed(self):
        self.assertEqual(self.validate(self.valid_payload()), "receipt")
        for field, value in (("generation", True), ("captured_epoch", True),
                             ("evidence", []), ("boundary", 7)):
            payload = self.valid_payload()
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(payload)
        for field, value in (("backup_completed_minute", True),
                             ("backup_verified", 1), ("news_quiesced", "true"),
                             ("source_observed", 1), ("consumers_quiesced", "aster-agent"),
                             ("backup_receipt", [])):
            payload = self.valid_payload()
            payload["evidence"][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.validate(payload)
        for section in (None, "evidence"):
            payload = self.valid_payload()
            target = payload if section is None else payload[section]
            target["extra"] = "unreviewed"
            with self.subTest(section=section), self.assertRaises(ValueError):
                self.validate(payload)

    def test_writer_rejects_unsafe_parent_before_touching_fixed_temp_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "receipt.json"
            sentinel = root / "sentinel"
            sentinel.write_text("unchanged")
            (root / "receipt.json.new").symlink_to(sentinel)
            os.chmod(root, 0o755)
            with patch("source_receipt_boundary.os.geteuid", return_value=0), \
                    self.assertRaisesRegex(ValueError, "directory custody"):
                _write_envelope(path, self.evidence(), lease_id="lab-1", generation=2, captured_epoch=100)
            self.assertEqual(sentinel.read_text(), "unchanged")
            self.assertFalse(path.exists())

    def test_writer_uses_unique_temp_and_keeps_previous_receipt_on_replace_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "receipt.json"
            sentinel = root / "sentinel"
            sentinel.write_text("unchanged")
            (root / "receipt.json.new").symlink_to(sentinel)
            path.write_text("old receipt")
            with patch("source_receipt_boundary.os.geteuid", return_value=0), \
                    patch("source_receipt_boundary._parent_custody"), \
                    patch("source_receipt_boundary._custody"), \
                    patch("source_receipt_boundary.os.replace", side_effect=OSError("synthetic failure")):
                with self.assertRaisesRegex(OSError, "synthetic failure"):
                    _write_envelope(path, self.evidence(), lease_id="lab-1", generation=2, captured_epoch=100)
            self.assertEqual(path.read_text(), "old receipt")
            self.assertEqual(sentinel.read_text(), "unchanged")
            self.assertEqual([p.name for p in root.iterdir() if p.name.startswith(".source-receipt-")], [])

    def test_producer_requires_lease_issue_time(self):
        import inspect
        self.assertIn("lease_issued_epoch", str(inspect.signature(__import__("source_receipt_boundary").produce_candidate_receipt)))

    def test_post_stop_producer_uses_retained_source_and_exact_lease_digest(self):
        class Adapter:
            def __init__(self, evidence):
                self.evidence = evidence
                self.calls = []

            def evidence_from_retained(self, **kwargs):
                self.calls.append(kwargs)
                return self.evidence

        adapter = Adapter(self.evidence())
        with patch("source_receipt_boundary.os.geteuid", return_value=0), patch("source_receipt_boundary._write_envelope") as write:
            produce_candidate_receipt(
                Path("/unused"), adapter, lease_id="lab-1", generation=1,
                date_prefix="2026_10_15", lease_issued_epoch=100,
                now_minute=221, window_end_minute=255, captured_epoch=101,
                expected_backup_receipt="receipt",
            )
            self.assertEqual(len(adapter.calls), 1)
            write.assert_called_once()
            with self.assertRaisesRegex(ValueError, "differs"):
                produce_candidate_receipt(
                    Path("/unused"), adapter, lease_id="lab-1", generation=1,
                    date_prefix="2026_10_15", lease_issued_epoch=100,
                    now_minute=221, window_end_minute=255, captured_epoch=101,
                    expected_backup_receipt="wrong",
                )
            write.assert_called_once()

    @unittest.skipUnless(os.geteuid() == 0, "requires root-owned custody test")
    def test_rejects_stale_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            _write_envelope(path, self.evidence(), lease_id="lab-1", generation=2, captured_epoch=100)
            with self.assertRaisesRegex(ValueError, "stale"):
                read_receipt(path, lease_id="lab-1", generation=2, now_minute=221, window_end_minute=255, now_epoch=1101)


if __name__ == "__main__":
    unittest.main()
