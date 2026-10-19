import tempfile
import unittest
from pathlib import Path

from unittest.mock import patch

from lab_workload_admission import (LabAdmissionError, LabAdmissionManifest,
                                    LabAdmissionRequest, LabAdmissionVerifier,
                                    DurableReplayStore)


class LabWorkloadAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = LabAdmissionManifest(
            "macbook-owner", "lease-7", 3, "SHA256:macbook-key",
            "a" * 64, "b" * 64, "c" * 64, 100, 200)
        self.request = LabAdmissionRequest(
            "macbook-owner", "lease-7", 3, "SHA256:macbook-key",
            "a" * 64, "b" * 64, "c" * 64, "req-abcdefghijklmnop")

    def test_matching_source_bound_request_is_admitted(self):
        with tempfile.TemporaryDirectory() as tmp, patch("lab_workload_admission.time.time", return_value=150):
            receipt = LabAdmissionVerifier(self.manifest, DurableReplayStore(Path(tmp) / "lease-7-3.json")).authorize(self.request)
        self.assertEqual(receipt["admitted"], True)
        self.assertNotIn("request_id", receipt)
        self.assertEqual(len(receipt["request_id_sha256"]), 64)

    def test_rejects_identity_generation_and_key_drift(self):
        for field, value in (("owner_id", "other"), ("generation", 4),
                             ("client_key_fingerprint", "SHA256:other"),
                             ("host_key_sha256", "d" * 64)):
            with self.subTest(field=field):
                request = self.request.__class__(**{**self.request.__dict__, field: value})
                with patch("lab_workload_admission.time.time", return_value=150):
                    with tempfile.TemporaryDirectory() as tmp:
                        with self.assertRaisesRegex(LabAdmissionError, "match"):
                            LabAdmissionVerifier(self.manifest, DurableReplayStore(Path(tmp) / "lease.json")).authorize(request)

    def test_rejects_source_profile_and_expiry_drift(self):
        for field, value in (("source_sha256", "d" * 64), ("profile_sha256", "d" * 64)):
            with self.subTest(field=field):
                request = self.request.__class__(**{**self.request.__dict__, field: value})
                with patch("lab_workload_admission.time.time", return_value=150):
                    with tempfile.TemporaryDirectory() as tmp:
                        with self.assertRaises(LabAdmissionError):
                            LabAdmissionVerifier(self.manifest, DurableReplayStore(Path(tmp) / "lease.json")).authorize(request)

    def test_rejects_invalid_manifest_digests_and_unbounded_window(self):
        bad = self.manifest.__class__(**{**self.manifest.__dict__, "host_key_sha256": "not-a-digest"})
        with self.assertRaisesRegex(LabAdmissionError, "host key"):
            LabAdmissionVerifier(bad, DurableReplayStore(Path("/tmp") / "bad.json"))
        bad = self.manifest.__class__(**{**self.manifest.__dict__, "issued_epoch": 200})
        with self.assertRaisesRegex(LabAdmissionError, "expiry"):
            LabAdmissionVerifier(bad, DurableReplayStore(Path("/tmp") / "bad.json"))

    def test_rejects_expiry_replay_and_unsafe_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            replay = DurableReplayStore(Path(tmp) / "lease-7-3.json")
            verifier = LabAdmissionVerifier(self.manifest, replay)
            with patch("lab_workload_admission.time.time", return_value=200):
                with self.assertRaisesRegex(LabAdmissionError, "outside"):
                    verifier.authorize(self.request)
            with patch("lab_workload_admission.time.time", return_value=150):
                verifier.authorize(self.request)
                restarted = LabAdmissionVerifier(self.manifest, DurableReplayStore(Path(tmp) / "lease-7-3.json"))
                with self.assertRaisesRegex(LabAdmissionError, "already"):
                    restarted.authorize(self.request)
            for value in ("", "secret-marker", "req-short"):
                with self.subTest(request_id=value):
                    request = self.request.__class__(**{**self.request.__dict__, "request_id": value})
                    with patch("lab_workload_admission.time.time", return_value=150):
                        with self.assertRaisesRegex(LabAdmissionError, "identity"):
                            LabAdmissionVerifier(self.manifest, replay).authorize(request)

    def test_rejects_overlong_session(self):
        bad = self.manifest.__class__(**{**self.manifest.__dict__, "expires_epoch": 100 + 45 * 60 + 1})
        with self.assertRaisesRegex(LabAdmissionError, "session bound"):
            LabAdmissionVerifier(bad, DurableReplayStore(Path("/tmp") / "bad.json"))


if __name__ == "__main__":
    unittest.main()
