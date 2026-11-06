from pathlib import Path
import tempfile
import unittest

import sa4_observer_signer_v1 as signer


def statement(**changes):
    value = {"schema": "aster-sa4-independent-receipt-proof.v1",
             "receipt_sha256": "a" * 64,
             "observer_id": signer.OBSERVER_ID,
             "observer_key_sha256": signer.KEY_SHA256,
             "signature_algorithm": "rsa-pkcs1v1_5-sha256",
             "authority": "observer-proof-only-no-effect"}
    value.update(changes); return signer.canonical(value)


class Result:
    returncode = 0; stdout = b"o" * 256; stderr = b""


class SA4ObserverSignerTests(unittest.TestCase):
    def test_fixed_invocation_and_signature_shape(self):
        observed = {}
        def runner(command, **options):
            observed.update(command=command, options=options); return Result()
        self.assertEqual("6f" * 256, signer.sign(statement(), runner=runner))
        self.assertEqual([signer.OPENSSL, "dgst", "-sha256", "-sign",
                          signer.KEY_PATH], observed["command"])

    def test_changed_identity_key_or_authority_fails_closed(self):
        for raw in (statement(observer_id="other"),
                    statement(observer_key_sha256="b" * 64),
                    statement(authority="effect"), b" " + statement()):
            with self.assertRaises(ValueError): signer.validate_statement(raw)

    def test_symlink_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            actual = Path(directory) / "actual"; actual.write_bytes(statement())
            link = Path(directory) / "link"; link.symlink_to(actual)
            with self.assertRaises(OSError): signer.read_statement(str(link))

    def test_no_export_or_arbitrary_key_interface(self):
        source = Path(signer.__file__).read_text()
        self.assertNotIn("BEGIN PRIVATE KEY", source)
        self.assertIn(signer.KEY_PATH, source)
        self.assertIn(signer.KEY_SHA256, source)


if __name__ == "__main__": unittest.main()
