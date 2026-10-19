import unittest

from lab_macbook_admission_adapter import (AuthenticatedMacBookSession,
                                           manifest_from_authenticated_session)
from lab_workload_admission import LabAdmissionError, validate_manifest


class LabMacBookAdmissionAdapterTests(unittest.TestCase):
    def session(self):
        return AuthenticatedMacBookSession("jelliott", "SHA256:clientFingerprint=", "a" * 64, "ssh-session-1")

    def kwargs(self):
        return dict(lease_id="lease-1", generation=2, source_sha256="b" * 64,
                    profile_sha256="c" * 64, issued_epoch=100, expires_epoch=200)

    def test_manifest_uses_authenticated_transport_identity(self):
        manifest = manifest_from_authenticated_session(self.session(), **self.kwargs())
        self.assertEqual(manifest.owner_id, "jelliott")
        self.assertEqual(manifest.client_key_fingerprint, "SHA256:clientFingerprint=")
        validate_manifest(manifest)

    def test_rejects_non_transport_principal_or_unsafe_session(self):
        for field, value in (("principal", "caller-json"), ("session_id", "bad space"),
                             ("client_key_fingerprint", "not-a-fingerprint")):
            with self.subTest(field=field):
                session = self.session().__class__(**{**self.session().__dict__, field: value})
                with self.assertRaisesRegex(LabAdmissionError, "authenticated"):
                    manifest_from_authenticated_session(session, **self.kwargs())

    def test_rejects_session_host_key_drift(self):
        session = self.session().__class__(**{**self.session().__dict__, "host_key_sha256": "z" * 64})
        with self.assertRaisesRegex(LabAdmissionError, "host key"):
            manifest_from_authenticated_session(session, **self.kwargs())


if __name__ == "__main__":
    unittest.main()
