import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from bundle_verifier import canonical_json, digest

@unittest.skipUnless(shutil.which("ssh-keygen"), "ssh-keygen is required")
class BundleValidateCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inbox = self.root / "inbox"
        self.inbox.mkdir()
        self.bundle_id = "A" * 22
        self.bundle = self.inbox / self.bundle_id
        self.bundle.mkdir()
        self.key = self.root / "key"
        subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(self.key)], check=True)
        self.allowed = self.root / "allowed_signers"
        self.allowed.write_text("cloud-producer " + (self.root / "key.pub").read_text())
        self.allowed.chmod(0o600)
        self.base, self.policy = "a" * 40, "b" * 64
        (self.root / "base").write_text(self.base + "\n")
        (self.root / "policy").write_text(self.policy + "\n")
        content = b"synthetic canary\n"
        (self.bundle / "content.txt").write_bytes(content)
        self.request = {
            "version": 1, "repository": "jason/homelab", "base_revision": self.base,
            "target_branch": "ai-pam/cloud-runner-canary", "nonce": self.bundle_id,
            "issued_at": int(time.time()) - 5, "expires_at": int(time.time()) + 300,
            "policy_digest": self.policy, "signer": "cloud-producer",
            "action": {"file_path": "ai-pam-pilot/cloud-runner/canary.txt",
                "content_file": "content.txt", "content_sha256": digest(content),
                "content_size": len(content), "commit_message": "AI-PAM pilot: isolated validator canary"},
        }
        self.sign()

    def tearDown(self):
        self.temp.cleanup()

    def sign(self):
        body = canonical_json(self.request)
        (self.bundle / "request.json").write_bytes(body)
        source = self.root / "body"
        source.write_bytes(body)
        (self.root / "body.sig").unlink(missing_ok=True)
        subprocess.run(["ssh-keygen", "-Y", "sign", "-f", str(self.key), "-n", "homelab-change-bundle", str(source)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (self.bundle / "request.sig").write_bytes((self.root / "body.sig").read_bytes())

    def run_cli(self, bundle_id=None):
        return subprocess.run([sys.executable, "bundle_validate.py", "--inbox", str(self.inbox), "--bundle-id", bundle_id or self.bundle_id, "--base-file", str(self.root / "base"), "--policy-file", str(self.root / "policy"), "--allowed-signers", str(self.allowed)], cwd=Path(__file__).parent, text=True, capture_output=True)

    def test_valid_signed_bundle_emits_metadata_only_receipt(self):
        result = self.run_cli()
        self.assertEqual(0, result.returncode, result.stderr)
        receipt = json.loads(result.stdout)
        self.assertEqual("validated", receipt["status"])
        self.assertNotIn("content", receipt)

    def test_tamper_and_invalid_instance_are_denied(self):
        (self.bundle / "content.txt").write_text("changed\n")
        self.assertIn("DENIED", self.run_cli().stderr)
        self.assertIn("identifier", self.run_cli("../escape").stderr)

if __name__ == "__main__":
    unittest.main()
