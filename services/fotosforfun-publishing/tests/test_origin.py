from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from origin_receiver import ReceiverError, verify
from origin_sender import DEFAULT_KEY, ssh_argv, validate
from renderer import write_manifest


class OriginBoundaryTests(unittest.TestCase):
    def test_receiver_accepts_exact_manifest_and_rejects_sample_marker(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary)
            (release / "index.html").write_text("<html>approved gallery</html>")
            digest = write_manifest(release)
            self.assertEqual(verify(release), digest)
            (release / "index.html").write_text("credited photographs are stand-ins")
            write_manifest(release)
            with self.assertRaisesRegex(ReceiverError, "sample"):
                verify(release)
            self.assertEqual(len(verify(release, allow_private_sample=True)), 64)

    def test_sender_is_pinned_to_fotosforfun_key_and_scope(self):
        valid = "fotosforfun-" + "a" * 12 + "-" + "b" * 12
        validate(valid)
        with self.assertRaisesRegex(ValueError, "Fotosforfun"):
            validate("contrast-e1-" + "b" * 12)
        argv = ssh_argv(["status"])
        self.assertIn(str(DEFAULT_KEY), argv)
        self.assertIn("fotosforfun-deploy@192.168.20.36", argv)
        self.assertIn("StrictHostKeyChecking=yes", argv)


if __name__ == "__main__":
    unittest.main()
