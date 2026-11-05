import json
import os
from pathlib import Path
import tempfile
import unittest

import sa4_one_use_grant_ledger_v1 as ledger


GRANT = "sa4-synthetic-grant"
PLAN_SHA = "1" * 64
GRANT_SHA = "2" * 64
TARGET_SHA = "3" * 64
EVIDENCE_SHA = "4" * 64


class SA4OneUseGrantLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "ledger"
        self.store = ledger.OneUseLedger(self.root, expected_uid=os.geteuid())

    def tearDown(self):
        self.temporary.cleanup()

    def initialize(self):
        return self.store.initialize(
            grant_id=GRANT, plan_sha256=PLAN_SHA, grant_sha256=GRANT_SHA,
            target_sha256=TARGET_SHA, now_epoch=100, expires_epoch=1000)

    def test_exact_grant_claim_and_terminal_consumption_are_one_use(self):
        self.initialize()
        claimed = self.store.claim(
            GRANT, claimant="sa4-owner-process", now_epoch=200,
            deadline_epoch=400)
        self.assertEqual("claimed", claimed["state"])
        self.assertEqual(1, claimed["use_count"])
        self.assertFalse(claimed["effect_authorized"])
        consumed = self.store.finish(
            GRANT, claimant="sa4-owner-process", state="consumed",
            evidence_sha256=EVIDENCE_SHA, now_epoch=300)
        self.assertEqual("consumed", consumed["state"])
        self.assertFalse(consumed["automatic_retry"])
        with self.assertRaises(ledger.LedgerError):
            self.store.claim(GRANT, claimant="sa4-owner-process",
                             now_epoch=301, deadline_epoch=350)
        with self.assertRaises(ledger.LedgerError):
            self.store.finish(
                GRANT, claimant="sa4-owner-process", state="consumed",
                evidence_sha256=EVIDENCE_SHA, now_epoch=302)

    def test_duplicate_initialize_claim_and_identity_drift_fail_closed(self):
        self.initialize()
        with self.assertRaises(ledger.LedgerError):
            self.initialize()
        self.store.claim(GRANT, claimant="sa4-owner-process",
                         now_epoch=200, deadline_epoch=400)
        with self.assertRaises(ledger.LedgerError):
            self.store.claim(GRANT, claimant="second-owner-process",
                             now_epoch=201, deadline_epoch=401)
        with self.assertRaises(ledger.LedgerError):
            self.store.finish(
                GRANT, claimant="wrong-owner-process", state="failed",
                evidence_sha256=EVIDENCE_SHA, now_epoch=300)

    def test_abandoned_claim_is_fenced_uncertain_and_never_reused(self):
        self.initialize()
        self.store.claim(GRANT, claimant="sa4-owner-process",
                         now_epoch=200, deadline_epoch=300)
        with self.assertRaises(ledger.LedgerError):
            self.store.fence_expired_claim(
                GRANT, now_epoch=300, evidence_sha256=EVIDENCE_SHA)
        uncertain = self.store.fence_expired_claim(
            GRANT, now_epoch=301, evidence_sha256=EVIDENCE_SHA)
        self.assertEqual("uncertain", uncertain["state"])
        self.assertEqual(1, uncertain["use_count"])
        with self.assertRaises(ledger.LedgerError):
            self.store.claim(GRANT, claimant="sa4-owner-process",
                             now_epoch=302, deadline_epoch=350)

    def test_late_claim_cannot_be_recorded_as_consumed_success(self):
        self.initialize()
        self.store.claim(GRANT, claimant="sa4-owner-process",
                         now_epoch=200, deadline_epoch=300)
        with self.assertRaises(ledger.LedgerError):
            self.store.finish(
                GRANT, claimant="sa4-owner-process", state="consumed",
                evidence_sha256=EVIDENCE_SHA, now_epoch=301)
        failed = self.store.finish(
            GRANT, claimant="sa4-owner-process", state="failed",
            evidence_sha256=EVIDENCE_SHA, now_epoch=301)
        self.assertEqual("failed", failed["state"])

    def test_expiry_deadline_and_digest_bounds_fail_closed(self):
        with self.assertRaises(ledger.LedgerError):
            self.store.initialize(
                grant_id=GRANT, plan_sha256=PLAN_SHA,
                grant_sha256=GRANT_SHA, target_sha256=TARGET_SHA,
                now_epoch=100, expires_epoch=3701)
        self.initialize()
        for now, deadline in ((1000, 1001), (200, 1101), (200, 200)):
            with self.subTest(now=now, deadline=deadline), self.assertRaises(
                    ledger.LedgerError):
                self.store.claim(GRANT, claimant="sa4-owner-process",
                                 now_epoch=now, deadline_epoch=deadline)

    def test_record_mode_symlink_link_and_canonical_drift_fail_closed(self):
        self.initialize()
        record = self.root / "records" / f"{GRANT}.json"
        os.chmod(record, 0o644)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)
        os.chmod(record, 0o600)
        linked = self.root / "records" / "linked.json"
        os.link(record, linked)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)
        linked.unlink()
        value = json.loads(record.read_text())
        record.write_text(json.dumps(value, indent=2) + "\n")
        os.chmod(record, 0o600)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)
        record.unlink()
        outside = Path(self.temporary.name) / "outside.json"
        outside.write_text("{}\n"); os.chmod(outside, 0o600)
        record.symlink_to(outside)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)

    def test_directory_and_lock_custody_drift_fail_closed(self):
        self.initialize()
        os.chmod(self.root / "ledger.lock", 0o644)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)
        os.chmod(self.root / "ledger.lock", 0o600)
        os.chmod(self.root / "records", 0o755)
        with self.assertRaises(ledger.LedgerError):
            self.store.get(GRANT)


if __name__ == "__main__":
    unittest.main()
