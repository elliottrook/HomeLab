import hashlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from bundle_verifier import ReplayLedger
from project_document_bundle_runner import (
    ProjectDocumentBundleRunner, cli_main, promotion_payload,
)
from project_document_bundle_verifier import canonical_json


BASE = "a" * 40
POLICY = "b" * 64
NOW = 1_800_000_000
NONCE = "n" * 24


class ProjectDocumentBundleRunnerTests(unittest.TestCase):
    def make_bundle(self):
        root = Path(tempfile.mkdtemp())
        (root / "files/docs/projects").mkdir(parents=True)
        (root / "files/docs/projects/example.md").write_text("# Example\n", encoding="utf-8")
        content = b"# Example\n"
        request = {
            "version": 1, "repository": "jason/homelab", "base_revision": BASE,
            "target_branch": "ai-pam/project-example", "nonce": NONCE,
            "issued_at": NOW - 10, "expires_at": NOW + 100,
            "policy_digest": POLICY, "signer": "cloud-producer",
            "action": {
                "files": [{"path": "docs/projects/example.md",
                           "content_sha256": hashlib.sha256(content).hexdigest(),
                           "content_size": len(content)}],
                "commit_message": "AI-PAM project: example",
            },
        }
        (root / "manifest.json").write_bytes(canonical_json(request))
        (root / "manifest.sig").write_bytes(b"signature")
        return root

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.source = self.make_bundle()
        self.handoff = root / "handoff"
        self.handoff.mkdir()
        self.ledger = ReplayLedger(root / "ledger.sqlite")
        self.requests = []

        def broker(request):
            self.requests.append(request)
            if request["method"] == "request.create":
                return {"status": "pending", "request_id": "11111111-1111-1111-1111-111111111111"}
            return {"status": "consumed", "request_id": request["request_id"]}

        self.runner = ProjectDocumentBundleRunner(
            self.ledger, broker, self.handoff, clock=lambda: NOW,
        )

    def tearDown(self):
        self.ledger.close()
        self.tempdir.cleanup()

    def verify_signature(self, body, signature, signer):
        return signature == b"signature" and signer == "cloud-producer"

    def test_submit_stages_content_and_approval_contains_metadata_only(self):
        pending = self.runner.submit(
            self.source, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.verify_signature,
        )
        self.assertTrue((pending.handoff_dir / "files/docs/projects/example.md").exists())
        payload = self.requests[0]["payload"]
        self.assertEqual("forgejo.write.project-documents", self.requests[0]["capability"])
        self.assertIn("content_sha256", payload["files"][0])
        self.assertNotIn("content", payload["files"][0])

    def test_promote_rechecks_handoff_and_consumes_once(self):
        pending = self.runner.submit(
            self.source, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.verify_signature,
        )
        result = self.runner.promote(pending, current_base_revision=BASE, policy_digest=POLICY)
        self.assertEqual("consumed", result["status"])
        self.assertEqual("request.consume", self.requests[-1]["method"])

    def test_promote_denies_handoff_tamper(self):
        pending = self.runner.submit(
            self.source, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.verify_signature,
        )
        (pending.handoff_dir / "files/docs/projects/example.md").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(Exception):
            self.runner.promote(pending, current_base_revision=BASE, policy_digest=POLICY)
        self.assertEqual(1, len(self.requests))

    def test_payload_is_stable_and_branch_is_non_main(self):
        pending = self.runner.submit(
            self.source, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.verify_signature,
        )
        payload = promotion_payload(pending.verified)
        self.assertEqual("main", payload["branch_name"])
        self.assertTrue(str(payload["new_branch_name"]).startswith("ai-pam/"))

    def test_cli_submit_and_promote_emit_metadata_only(self):
        root = Path(self.tempdir.name)
        base_file = root / "base_revision"
        policy_file = root / "policy_digest"
        base_file.write_text(BASE + "\n", encoding="ascii")
        policy_file.write_text(POLICY + "\n", encoding="ascii")
        (root / "cli-handoff").mkdir()
        broker_calls = []

        def broker(_socket, request):
            broker_calls.append(request)
            if request["method"] == "request.create":
                return {
                    "status": "pending",
                    "request_id": "22222222-2222-2222-2222-222222222222",
                }
            return {"status": "consumed", "request_id": request["request_id"]}

        output = io.StringIO()
        with patch(
            "project_document_bundle_runner._cli_signature_verifier",
            return_value=self.verify_signature,
        ), patch(
            "project_document_bundle_runner.broker_call",
            side_effect=broker,
        ), patch(
            "project_document_bundle_runner.time.time",
            return_value=NOW,
        ), redirect_stdout(output):
            submit_rc = cli_main([
                "submit", "--bundle-dir", str(self.source),
                "--ledger", str(root / "cli-ledger.sqlite"),
                "--broker-socket", str(root / "unused.sock"),
                "--handoff-root", str(root / "cli-handoff"),
                "--base-file", str(base_file),
                "--policy-file", str(policy_file),
                "--allowed-signers", str(root / "unused-signers"),
            ])
            promote_rc = cli_main([
                "promote", "--bundle-dir", str(self.source),
                "--ledger", str(root / "cli-ledger.sqlite"),
                "--broker-socket", str(root / "unused.sock"),
                "--handoff-root", str(root / "cli-handoff"),
                "--base-file", str(base_file),
                "--policy-file", str(policy_file),
                "--allowed-signers", str(root / "unused-signers"),
            ])

        self.assertEqual(0, submit_rc)
        self.assertEqual(0, promote_rc)
        self.assertEqual(["request.create", "request.consume"], [
            request["method"] for request in broker_calls
        ])
        self.assertNotIn("# Example", output.getvalue())
        self.assertIn('"status":"pending"', output.getvalue())
        self.assertIn('"status":"consumed"', output.getvalue())


if __name__ == "__main__":
    unittest.main()
