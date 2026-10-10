import tempfile
import unittest
from pathlib import Path

from bundle_runner import BrokerDenied, BundleRunner, PendingBundle
from bundle_verifier import ReplayLedger, canonical_json, digest


BASE = "a" * 40
POLICY = "b" * 64
NOW = 2_000_000_000


class FakeBroker:
    def __init__(self):
        self.calls = []
        self.approved = False

    def __call__(self, request):
        self.calls.append(request)
        if request["method"] == "request.create":
            return {"request_id": "12345678-1234-1234-1234-123456789abc", "status": "pending"}
        if request["method"] == "request.consume" and self.approved:
            return {"request_id": request["request_id"], "status": "consumed", "result": {"ok": True}}
        raise BrokerDenied("broker denied the request")


class BundleRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        content = b"synthetic canary\n"
        (self.root / "content.txt").write_bytes(content)
        request = {
            "version": 1, "repository": "jason/homelab", "base_revision": BASE,
            "target_branch": "ai-pam/cloud-runner-canary", "nonce": "A" * 22,
            "issued_at": NOW - 10, "expires_at": NOW + 300,
            "policy_digest": POLICY, "signer": "cloud-producer",
            "action": {
                "file_path": "ai-pam-pilot/cloud-runner/canary.txt",
                "content_file": "content.txt", "content_sha256": digest(content),
                "content_size": len(content),
                "commit_message": "AI-PAM pilot: cloud runner canary",
            },
        }
        (self.root / "request.json").write_bytes(canonical_json(request))
        (self.root / "request.sig").write_bytes(b"test-signature")
        self.ledger = ReplayLedger(self.root / "ledger.sqlite")
        self.broker = FakeBroker()
        self.runner = BundleRunner(self.ledger, self.broker, clock=lambda: NOW)
        self.signature = lambda body, signature, principal: signature == b"test-signature" and principal == "cloud-producer"

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def test_submit_requires_later_approval_and_uses_exact_payload(self):
        pending = self.runner.submit(
            self.root, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.signature,
        )
        self.assertIsInstance(pending, PendingBundle)
        self.assertEqual("request.create", self.broker.calls[0]["method"])
        with self.assertRaises(BrokerDenied):
            self.runner.promote(
                pending, bundle_dir=self.root, current_base_revision=BASE,
                policy_digest=POLICY,
            )

    def test_approved_request_consumes_once(self):
        pending = self.runner.submit(
            self.root, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.signature,
        )
        self.broker.approved = True
        result = self.runner.promote(
            pending, bundle_dir=self.root, current_base_revision=BASE,
            policy_digest=POLICY,
        )
        self.assertEqual("consumed", result["status"])
        with self.assertRaisesRegex(ValueError, "not pending"):
            self.runner.promote(
                pending, bundle_dir=self.root, current_base_revision=BASE,
                policy_digest=POLICY,
            )

    def test_changed_base_stops_before_broker_consume(self):
        pending = self.runner.submit(
            self.root, current_base_revision=BASE, policy_digest=POLICY,
            verify_signature=self.signature,
        )
        self.broker.approved = True
        count = len(self.broker.calls)
        with self.assertRaisesRegex(ValueError, "base revision"):
            self.runner.promote(
                pending, bundle_dir=self.root, current_base_revision="c" * 40,
                policy_digest=POLICY,
            )
        self.assertEqual(count, len(self.broker.calls))


if __name__ == "__main__":
    unittest.main()
