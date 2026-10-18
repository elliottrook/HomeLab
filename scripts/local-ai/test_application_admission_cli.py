import unittest
from unittest.mock import patch

import application_admission_cli
from application_receipt_boundary import A1_PROFILE_SHA256


class ApplicationAdmissionCliTests(unittest.TestCase):
    def test_rejects_wrong_profile_before_boundary(self):
        with patch("application_admission_cli.os.geteuid", return_value=0), \
             patch("application_admission_cli.host_admission_callback") as callback:
            with self.assertRaisesRegex(SystemExit, "profile pin"):
                application_admission_cli.main(["--profile", "0" * 64])
            callback.assert_not_called()

    def test_projects_only_boundary_payload(self):
        payload = {"schema": "aster-a1-admission.v2", "lease_id": "lease-1",
                   "generation": 2, "receipt_sha256": "a" * 64,
                   "profile_sha256": A1_PROFILE_SHA256,
                   "endpoint": "http://192.168.70.10:19104/v1/chat/completions"}
        with patch("application_admission_cli.os.geteuid", return_value=0), \
             patch("application_admission_cli.host_admission_callback", return_value=payload):
            self.assertEqual(application_admission_cli.main(["--profile", A1_PROFILE_SHA256]), 0)


if __name__ == "__main__":
    unittest.main()
