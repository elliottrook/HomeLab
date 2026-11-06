import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

import sa4_distinct_canary_plan_v1 as plan_source
import sa4_preclaim_failure_reconciler_v1 as source
import sa4_single_file_repair_contract_v1 as contract


class PreclaimReconcilerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.paths = {
            "TARGET_PATH": root / "target",
            "INPUT_DIR": root / "input",
            "EVIDENCE_DIR": root / "evidence",
            "LEDGER_RECORD": root / "ledger" / "records" / "grant.json",
            "CHECKPOINT_PATH": root / "checkpoints" / "retained.original",
            "CHECKPOINT_TEMP": root / "checkpoints" / ".checkpoint.tmp",
            "EXCHANGE_DIR": root / "exchange",
            "LOCK_PATH": root / "operation.lock",
            "STOP_PATH": root / "emergency-stop",
        }
        for name in ("INPUT_DIR", "EVIDENCE_DIR", "EXCHANGE_DIR"):
            self.paths[name].mkdir(mode=0o700, parents=True)
        self.paths["LEDGER_RECORD"].parent.mkdir(mode=0o700, parents=True)
        self.paths["CHECKPOINT_PATH"].parent.mkdir(mode=0o700, parents=True)
        drifted = (Path(__file__).parent / "fixtures" /
                   "sa4-canary-adapter-v2-drifted.json").read_bytes()
        self.assertEqual(source.TARGET_SHA256, hashlib.sha256(drifted).hexdigest())
        self.paths["TARGET_PATH"].write_bytes(drifted)
        self.paths["TARGET_PATH"].chmod(0o644)
        self.paths["CHECKPOINT_PATH"].write_bytes(drifted)
        self.paths["CHECKPOINT_PATH"].chmod(0o600)
        (self.paths["INPUT_DIR"] / "plan").write_bytes(plan_source.build_plan())
        (self.paths["INPUT_DIR"] / "plan").chmod(0o600)
        ledger = {
            "schema": "aster-sa4-one-use-grant-ledger.v1",
            "grant_id": source.GRANT_ID, "plan_sha256": source.PLAN_SHA256,
            "grant_sha256": "1" * 64, "target_registration_sha256": "2" * 64,
            "target_sha256": source.TARGET_SHA256, "created_epoch": 10,
            "expires_epoch": 900, "state": "ready", "use_count": 0,
            "automatic_retry": False, "authority": "one-use-ledger-only",
            "effect_authorized": False,
        }
        self.paths["LEDGER_RECORD"].write_bytes(contract.canonical(ledger))
        self.paths["LEDGER_RECORD"].chmod(0o600)
        lock = contract.canonical({
            "schema": "aster-sa4-operation-lock.v1", "plan_id": source.PLAN_ID,
            "plan_sha256": source.PLAN_SHA256})
        stop = contract.canonical({
            "schema": "aster-sa4-emergency-stop.v1", "plan_id": source.PLAN_ID,
            "plan_sha256": source.PLAN_SHA256, "state": "armed"})
        self.paths["LOCK_PATH"].write_bytes(lock); self.paths["LOCK_PATH"].chmod(0o600)
        self.paths["STOP_PATH"].write_bytes(stop); self.paths["STOP_PATH"].chmod(0o600)
        self.paths["RECEIPT_PATH"] = self.paths["EVIDENCE_DIR"] / "receipt.json"
        patches = {name: mock.patch.object(source, name, path)
                   for name, path in self.paths.items()}
        self.patchers = list(patches.values())
        for patcher in self.patchers:
            patcher.start()
        self.identity_patchers = [
            mock.patch.object(source, "EXPECTED_UID", os.getuid()),
            mock.patch.object(source, "EXPECTED_GID", os.getgid()),
        ]
        for patcher in self.identity_patchers:
            patcher.start()

    def tearDown(self):
        for patcher in reversed(self.identity_patchers + self.patchers):
            patcher.stop()
        self.temp.cleanup()

    def test_exact_preclaim_failure_is_recorded_and_controls_released(self):
        raw = source.reconcile(observed_epoch=77)
        value = json.loads(raw)
        self.assertEqual("CHECKPOINT_PATH_COLLISION", value["failure_class"])
        self.assertEqual(0, value["repair_effects"])
        self.assertFalse(self.paths["LOCK_PATH"].exists())
        self.assertFalse(self.paths["STOP_PATH"].exists())
        self.assertTrue(self.paths["RECEIPT_PATH"].exists())
        self.assertTrue(self.paths["CHECKPOINT_PATH"].exists())

    def test_target_drift_fails_without_cleanup(self):
        self.paths["TARGET_PATH"].write_bytes(b"changed\n")
        with self.assertRaisesRegex(ValueError, "target or retained checkpoint"):
            source.reconcile(observed_epoch=77)
        self.assertTrue(self.paths["LOCK_PATH"].exists())
        self.assertTrue(self.paths["STOP_PATH"].exists())

    def test_nonempty_evidence_fails_without_cleanup(self):
        (self.paths["EVIDENCE_DIR"] / "unexpected").write_text("x")
        with self.assertRaisesRegex(ValueError, "expected an empty directory"):
            source.reconcile(observed_epoch=77)
        self.assertTrue(self.paths["LOCK_PATH"].exists())
        self.assertTrue(self.paths["STOP_PATH"].exists())


if __name__ == "__main__":
    unittest.main()
