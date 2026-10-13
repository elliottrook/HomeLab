import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from bundle_verifier import (
    Denied, ReplayLedger, canonical_json, digest, reverify_for_promotion,
    verify_bundle, verify_openssh_signature,
)


BASE = "a" * 40
POLICY = "b" * 64
NOW = 2_000_000_000


class BundleVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.content = b"synthetic canary\n"
        (self.root / "content.txt").write_bytes(self.content)
        self.request = {
            "version": 1,
            "repository": "jason/homelab",
            "base_revision": BASE,
            "target_branch": "ai-pam/cloud-runner-canary",
            "nonce": "A" * 22,
            "issued_at": NOW - 10,
            "expires_at": NOW + 300,
            "policy_digest": POLICY,
            "signer": "cloud-producer",
            "action": {
                "file_path": "ai-pam-pilot/cloud-runner/canary.txt",
                "content_file": "content.txt",
                "content_sha256": digest(self.content),
                "content_size": len(self.content),
                "commit_message": "AI-PAM pilot: cloud runner canary",
            },
        }
        self.write_request()

    def tearDown(self):
        self.temp.cleanup()

    def write_request(self):
        (self.root / "request.json").write_bytes(canonical_json(self.request))
        (self.root / "request.sig").write_bytes(b"test-signature")

    def verify(self, **kwargs):
        return verify_bundle(
            self.root,
            current_base_revision=kwargs.pop("base", BASE),
            policy_digest=kwargs.pop("policy", POLICY),
            verify_signature=lambda body, signature, principal: (
                signature == b"test-signature" and principal == "cloud-producer"
            ),
            now=NOW,
            **kwargs,
        )

    def test_valid_bundle_maps_only_to_existing_safe_write_schema(self):
        result = self.verify()
        self.assertEqual(
            {"owner", "repo", "filePath", "content", "message", "branch_name", "new_branch_name"},
            set(result.payload),
        )
        self.assertEqual("main", result.payload["branch_name"])
        self.assertEqual("synthetic canary\n", result.payload["content"])

    def test_signature_and_signer_are_bound(self):
        self.request["signer"] = "someone-else"
        self.write_request()
        with self.assertRaisesRegex(Denied, "signature or signer"):
            self.verify()

    def test_stale_base_and_policy_are_denied(self):
        with self.assertRaisesRegex(Denied, "base revision"):
            self.verify(base="c" * 40)
        with self.assertRaisesRegex(Denied, "policy digest"):
            self.verify(policy="d" * 64)

    def test_expired_future_and_long_lived_are_denied(self):
        for issued, expires in ((NOW - 10, NOW), (NOW + 31, NOW + 100), (NOW, NOW + 901)):
            with self.subTest(issued=issued, expires=expires):
                self.request["issued_at"], self.request["expires_at"] = issued, expires
                self.write_request()
                with self.assertRaisesRegex(Denied, "expired, future-dated, or too long-lived"):
                    self.verify()

    def test_repository_branch_path_and_artifact_name_are_fixed(self):
        cases = (
            ("repository", "attacker/repo"),
            ("target_branch", "main"),
            ("action.file_path", "docs/escape.md"),
            ("action.content_file", "../content.txt"),
        )
        for key, value in cases:
            with self.subTest(key=key):
                original = json.loads(json.dumps(self.request))
                if key.startswith("action."):
                    self.request["action"][key.split(".")[1]] = value
                else:
                    self.request[key] = value
                self.write_request()
                with self.assertRaises(Denied):
                    self.verify()
                self.request = original

    def test_symlink_and_tampering_are_denied(self):
        result = self.verify()
        (self.root / "content.txt").write_bytes(b"changed\n")
        with self.assertRaisesRegex(Denied, "changed after validation"):
            reverify_for_promotion(
                result, bundle_dir=self.root, current_base_revision=BASE,
                policy_digest=POLICY, now=NOW,
            )
        (self.root / "content.txt").unlink()
        os.symlink(self.root / "request.json", self.root / "content.txt")
        with self.assertRaises(Denied):
            self.verify()

    def test_binary_secret_like_and_oversized_content_are_denied(self):
        for content in (b"\xff\xfe", b"api_key=do-not-log\n", b"x" * 4097):
            with self.subTest(length=len(content)):
                (self.root / "content.txt").unlink(missing_ok=True)
                (self.root / "content.txt").write_bytes(content)
                self.request["action"]["content_sha256"] = digest(content)
                self.request["action"]["content_size"] = len(content)
                self.write_request()
                with self.assertRaises(Denied):
                    self.verify()

    def test_replay_ledger_transitions_are_single_use(self):
        result = self.verify()
        ledger = ReplayLedger(self.root / "ledger.sqlite")
        ledger.reserve(result, NOW)
        with self.assertRaisesRegex(Denied, "already recorded"):
            ledger.reserve(result, NOW)
        request_id = "12345678-1234-1234-1234-123456789abc"
        ledger.bind_broker_request(result.nonce, result.request_digest, request_id, NOW)
        ledger.consume(result.nonce, result.request_digest, NOW)
        with self.assertRaisesRegex(Denied, "wrong state"):
            ledger.consume(result.nonce, result.request_digest, NOW)
        ledger.close()

    def test_revoke_is_terminal(self):
        result = self.verify()
        ledger = ReplayLedger(self.root / "ledger.sqlite")
        ledger.reserve(result, NOW)
        ledger.revoke(result.nonce, result.request_digest, NOW)
        with self.assertRaisesRegex(Denied, "wrong state"):
            ledger.bind_broker_request(
                result.nonce, result.request_digest,
                "12345678-1234-1234-1234-123456789abc", NOW,
            )
        ledger.close()

    @unittest.skipUnless(shutil.which("ssh-keygen"), "ssh-keygen is required")
    def test_real_openssh_signature_binds_namespace_and_principal(self):
        key = self.root / "signing-key"
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
            check=True,
        )
        allowed = self.root / "allowed_signers"
        allowed.write_text("cloud-producer " + (self.root / "signing-key.pub").read_text())
        allowed.chmod(0o600)
        body = canonical_json(self.request)
        body_file = self.root / "body.json"
        body_file.write_bytes(body)
        subprocess.run(
            ["ssh-keygen", "-Y", "sign", "-f", str(key), "-n", "homelab-change-bundle", str(body_file)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        signature = (self.root / "body.json.sig").read_bytes()
        self.assertTrue(verify_openssh_signature(
            body, signature, allowed_signers=allowed, principal="cloud-producer",
            binary=shutil.which("ssh-keygen") or "/usr/bin/ssh-keygen",
        ))
        self.assertFalse(verify_openssh_signature(
            body, signature, allowed_signers=allowed, principal="other-producer",
            binary=shutil.which("ssh-keygen") or "/usr/bin/ssh-keygen",
        ))
        self.assertFalse(verify_openssh_signature(
            body, signature, allowed_signers=allowed, principal="cloud-producer",
            namespace="wrong-namespace", binary=shutil.which("ssh-keygen") or "/usr/bin/ssh-keygen",
        ))


if __name__ == "__main__":
    unittest.main()
