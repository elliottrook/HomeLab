import json
from pathlib import Path
import tempfile
import unittest

import sa4_ai_pam_signer_v1 as signer


def statement(**changes) -> bytes:
    value = {
        "schema": "aster-sa4-detached-proof.v1",
        "proof_scope": "ai-pam-grant",
        "signer_id": signer.SIGNER_ID,
        "signer_key_sha256": signer.KEY_SHA256,
        "payload_sha256": "a" * 64,
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "signature-only-no-effect",
    }
    value.update(changes)
    return signer.canonical(value)


class Result:
    returncode = 0
    stdout = b"s" * 256
    stderr = b""


class SA4AIPAMSignerTests(unittest.TestCase):
    def test_fixed_signer_invocation_and_signature_shape(self):
        observed = {}

        def runner(command, **options):
            observed["command"] = command
            observed["options"] = options
            return Result()

        raw = statement()
        self.assertEqual("73" * 256, signer.sign(raw, runner=runner))
        self.assertEqual([signer.OPENSSL, "dgst", "-sha256", "-sign",
                          signer.KEY_PATH], observed["command"])
        self.assertEqual(raw, observed["options"]["input"])
        self.assertTrue(observed["options"]["capture_output"])

    def test_changed_scope_identity_key_or_noncanonical_bytes_fail_closed(self):
        cases = (
            statement(proof_scope="owner-approval"),
            statement(signer_id="other-signer"),
            statement(signer_key_sha256="b" * 64),
            b" " + statement(),
        )
        for raw in cases:
            with self.subTest(raw=raw[:40]):
                with self.assertRaises(ValueError):
                    signer.validate_statement(raw)

    def test_read_refuses_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            actual = Path(directory) / "actual.json"
            link = Path(directory) / "link.json"
            actual.write_bytes(statement())
            link.symlink_to(actual)
            with self.assertRaises(OSError): signer.read_statement(str(link))

    def test_no_export_or_arbitrary_key_interface(self):
        source = Path(signer.__file__).read_text()
        self.assertNotIn("BEGIN PRIVATE KEY", source)
        self.assertNotIn('case "export"', source)
        self.assertIn(signer.KEY_PATH, source)
        self.assertIn(signer.KEY_SHA256, source)


if __name__ == "__main__":
    unittest.main()
