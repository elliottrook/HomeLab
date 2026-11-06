from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))

import nlu_j2_custody_kit_v1 as kit
import nlu_j2_external_proof_v1 as external


@unittest.skipUnless(shutil.which("openssl"), "openssl is required")
class CustodyKitTests(unittest.TestCase):
    def test_keygen_and_signature_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_key = root / "private.pem"
            public_key = root / "public.json"
            result = kit.create_key(private_key, public_key)
            key = kit.public_key(private_key)
            self.assertEqual(result["public_key_sha256"], external.key_sha256(key))
            self.assertEqual(private_key.stat().st_mode & 0o777, 0o600)
            payload = b'{"content_in_receipt":false}\n'
            proof = kit.sign(payload, private_key, key,
                             "independent-j2-corpus-custodian",
                             "corpus-custody")
            verified = external.verify(
                proof, payload, key, external.key_sha256(key), "corpus-custody")
            self.assertTrue(verified["signature_verified"])

    def test_key_targets_are_create_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private_key = root / "private.pem"
            public_key = root / "public.json"
            kit.create_key(private_key, public_key)
            with self.assertRaisesRegex(ValueError, "already exists"):
                kit.create_key(private_key, public_key)


if __name__ == "__main__":
    unittest.main()
