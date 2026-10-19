import unittest

from lab_workload_admission import (LabAdmissionError, LabAdmissionManifest,
                                    LabAdmissionRequest, authorize_request)


class LabWorkloadAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = LabAdmissionManifest(
            "macbook-owner", "lease-7", 3, "SHA256:macbook-key",
            "a" * 64, "b" * 64, "c" * 64, 100, 200)
        self.request = LabAdmissionRequest(
            "macbook-owner", "lease-7", 3, "SHA256:macbook-key",
            "a" * 64, "b" * 64, "c" * 64, 150, "req-1")

    def test_matching_source_bound_request_is_admitted(self):
        receipt = authorize_request(self.manifest, self.request)
        self.assertEqual(receipt["admitted"], True)
        self.assertEqual(receipt["request_id"], "req-1")

    def test_rejects_identity_generation_and_key_drift(self):
        for field, value in (("owner_id", "other"), ("generation", 4),
                             ("client_key_fingerprint", "SHA256:other"),
                             ("host_key_sha256", "d" * 64)):
            with self.subTest(field=field):
                request = self.request.__class__(**{**self.request.__dict__, field: value})
                with self.assertRaisesRegex(LabAdmissionError, "match"):
                    authorize_request(self.manifest, request)

    def test_rejects_source_profile_and_expiry_drift(self):
        for field, value in (("source_sha256", "d" * 64), ("profile_sha256", "d" * 64),
                             ("now_epoch", 200)):
            with self.subTest(field=field):
                request = self.request.__class__(**{**self.request.__dict__, field: value})
                with self.assertRaises(LabAdmissionError):
                    authorize_request(self.manifest, request)

    def test_rejects_invalid_manifest_digests_and_unbounded_window(self):
        bad = self.manifest.__class__(**{**self.manifest.__dict__, "host_key_sha256": "not-a-digest"})
        with self.assertRaisesRegex(LabAdmissionError, "host key"):
            authorize_request(bad, self.request)
        bad = self.manifest.__class__(**{**self.manifest.__dict__, "issued_epoch": 200})
        with self.assertRaisesRegex(LabAdmissionError, "expiry"):
            authorize_request(bad, self.request)

    def test_rejects_request_before_lease_and_empty_request_id(self):
        for field, value in (("now_epoch", 99), ("request_id", "")):
            with self.subTest(field=field):
                request = self.request.__class__(**{**self.request.__dict__, field: value})
                with self.assertRaises(LabAdmissionError):
                    authorize_request(self.manifest, request)


if __name__ == "__main__":
    unittest.main()
