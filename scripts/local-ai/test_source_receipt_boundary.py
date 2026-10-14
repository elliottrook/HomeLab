import json
import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from admission_gate import EXPECTED_BACKUP_SOURCE, EXPECTED_CONSUMERS, AdmissionEvidence
from source_receipt_boundary import _write_envelope, read_receipt


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
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps({"boundary": "fake", "evidence": {}}))
            os.chmod(path, 0o600)
            with patch("source_receipt_boundary._custody"):
                with self.assertRaisesRegex(Exception, "boundary|lease"):
                    read_receipt(path, lease_id="lab-1", generation=1, now_minute=221, window_end_minute=255, now_epoch=101)

    @unittest.skipUnless(os.geteuid() == 0, "requires root-owned custody test")
    def test_rejects_stale_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            _write_envelope(path, self.evidence(), lease_id="lab-1", generation=2, captured_epoch=100)
            with self.assertRaisesRegex(ValueError, "stale"):
                read_receipt(path, lease_id="lab-1", generation=2, now_minute=221, window_end_minute=255, now_epoch=1101)


if __name__ == "__main__":
    unittest.main()
