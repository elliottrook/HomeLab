from hashlib import sha256
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from content import ContentError
import origin_sender


class SenderTests(unittest.TestCase):
    def test_ssh_is_pinned_and_command_is_argumentized(self):
        argv = origin_sender.ssh_argv(
            ["activate", "contrast", "contrast-e1-111111111111", "a" * 64],
            "deploy@example", Path("/key"), Path("/known"),
        )
        self.assertEqual(argv[-5:], ["deploy@example", "activate", "contrast",
                                     "contrast-e1-111111111111", "a" * 64])
        self.assertIn("StrictHostKeyChecking=yes", argv)
        self.assertIn("UserKnownHostsFile=/known", argv)

    @patch("origin_sender.subprocess.run")
    def test_activate_uses_only_validated_fields(self, run):
        origin_sender.request("activate", "closet", "closet-e4-abcdef123456", "b" * 64)
        run.assert_called_once()
        self.assertTrue(run.call_args.kwargs["check"])
        with self.assertRaises(ContentError):
            origin_sender.request("activate", "closet", "closet-e4-abcdef123456;id", "b" * 64)
        with self.assertRaises(ContentError):
            origin_sender.request("shell", "closet", "closet-e4-abcdef123456", "b" * 64)

    def test_stage_verifies_manifest_before_connecting(self):
        with tempfile.TemporaryDirectory() as temporary:
            release = Path(temporary)
            (release / "index.html").write_text("ready")
            digest = sha256((release / "index.html").read_bytes()).hexdigest()
            (release / "MANIFEST.sha256").write_text(f"{digest}  ./index.html\n")
            with patch("origin_sender.subprocess.Popen") as popen:
                process = popen.return_value
                process.stdin = open("/dev/null", "wb")
                process.wait.return_value = 0
                origin_sender.stage(release, "contrast", "contrast-e1-111111111111")
                self.assertIn("stage", popen.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
