import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bundle_health import check


class BundleHealthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.ledger = self.root / "ledger.sqlite"
        db = sqlite3.connect(self.ledger)
        db.execute("CREATE TABLE requests(nonce TEXT,state TEXT,updated_at INTEGER)")
        db.execute("INSERT INTO requests VALUES('one','consumed',995)")
        db.commit()
        db.close()
        self.base = self.root / "base"
        self.policy = self.root / "policy"
        self.signers = self.root / "signers"
        self.base.write_text("a" * 40 + "\n")
        self.policy.write_text("b" * 64 + "\n")
        self.signers.write_text("cloud-producer ssh-ed25519 test\n")
        for path in (self.base, self.policy, self.signers):
            os.chmod(path, 0o640)

    def tearDown(self):
        self.temp.cleanup()

    def test_reports_metadata_only_health(self):
        result = check(self.ledger, self.base, self.policy, self.signers,
                       now=1000, max_success_age=10)
        self.assertEqual("healthy", result["status"])
        self.assertEqual({"consumed": 1}, result["states"])
        self.assertNotIn("nonce", result)

    def test_stale_success_fails(self):
        with self.assertRaisesRegex(ValueError, "stale"):
            check(self.ledger, self.base, self.policy, self.signers,
                  now=1006, max_success_age=5)

    def test_writable_policy_fails(self):
        os.chmod(self.base, 0o660)
        with self.assertRaisesRegex(ValueError, "permissions"):
            check(self.ledger, self.base, self.policy, self.signers,
                  now=1000, max_success_age=10)
