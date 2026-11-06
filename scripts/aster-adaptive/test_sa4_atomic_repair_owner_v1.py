from dataclasses import replace
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_atomic_repair_owner_v1 as owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4AtomicRepairOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.before = b"drifted synthetic bytes\n"
        self.after = b"healthy synthetic bytes\n"
        self.target_path = root / "canary.json"
        self.target_path.write_bytes(self.before); os.chmod(self.target_path, 0o644)
        checkpoints = root / "checkpoints"; checkpoints.mkdir(mode=0o700)
        fixture = registry.SCHEMA_FIXTURES[0]
        self.target = replace(
            fixture, host_id="sa4-rehearsal-host", path=str(self.target_path),
            checkpoint_parent=str(checkpoints),
            temporary_path=str(root / ".canary.sa4-tmp"), maximum_bytes=4096)
        value = plan()
        value["target_id"] = self.target.target_id
        value["target"] = {"host_id": self.target.host_id,
                           "path": self.target.path, "type": "regular-file",
                           "follow_symlinks": False, "owner": "root",
                           "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = hashlib.sha256(self.before).hexdigest()
        value["change"]["artifact_sha256"] = hashlib.sha256(self.after).hexdigest()
        self.plan_raw = contract.canonical(value)
        self.registration = registry.registration_sha256(self.target)
        self.checkpoint_path = checkpoints / f"{value['plan_id']}.original"
        self.checkpoint_path.write_bytes(self.before); os.chmod(self.checkpoint_path, 0o600)
        self.checkpoint = {
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": owner.sha256(self.plan_raw),
            "measurement_sha256": "1" * 64,
            "target_id": self.target.target_id,
            "target_registration_sha256": self.registration,
            "checkpoint_epoch": 100, "checkpoint_path": str(self.checkpoint_path),
            "checkpoint_sha256": hashlib.sha256(self.before).hexdigest(),
            "checkpoint_mode": "0600", "checkpoint_link_count": 1,
            "checkpoint_same_filesystem": True, "target_unchanged": True,
            "exclusive_owner_lock": "held-during-create",
            "checkpoint_created": True, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False,
        }
        self.checkpoint_raw = contract.canonical(self.checkpoint)
        self.claim = {
            "schema": "aster-sa4-one-use-grant-ledger.v1",
            "grant_id": "sa4-rehearsal-grant",
            "plan_sha256": owner.sha256(self.plan_raw), "grant_sha256": "2" * 64,
            "target_registration_sha256": self.registration,
            "target_sha256": hashlib.sha256(self.before).hexdigest(),
            "created_epoch": 90, "expires_epoch": 200, "state": "claimed",
            "use_count": 1, "automatic_retry": False,
            "authority": "one-use-ledger-only", "effect_authorized": False,
            "claimant": "sa4-rehearsal-operation", "claimed_epoch": 100,
            "claim_deadline_epoch": 160,
        }
        self.claim_raw = contract.canonical(self.claim)
        self.admission = {
            "schema": "aster-sa4-effect-admission.v1",
            "plan_sha256": owner.sha256(self.plan_raw),
            "checkpoint_sha256": owner.sha256(self.checkpoint_raw),
            "claim_sha256": owner.sha256(self.claim_raw),
            "candidate_sha256": hashlib.sha256(self.after).hexdigest(),
            "target_registration_sha256": self.registration,
            "owner_effect_approval_sha256": "3" * 64,
            "expires_epoch": 150, "effect_authorized": True,
            "maximum_effects": 1, "automatic_retry": False,
            "automatic_routing": "off",
        }
        self.admission_raw = contract.canonical(self.admission)

    def tearDown(self): self.temporary.cleanup()

    def context(self):
        return patch.multiple(
            owner, LOCAL_HOST_ID=self.target.host_id,
            EXPECTED_UID=os.geteuid(), EXPECTED_GID=os.getegid())

    def execute(self):
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), self.context():
            return owner.execute(
                self.plan_raw, self.admission_raw, self.checkpoint_raw,
                self.claim_raw, self.after,
                operation_id="sa4-rehearsal-operation", effect_epoch=120)

    def test_atomic_rehearsal_replaces_once_and_returns_terminal(self):
        result = self.execute()
        self.assertEqual(self.after, self.target_path.read_bytes())
        self.assertEqual(1, result["effect_count"])
        self.assertEqual(0, result["retry_count"])
        self.assertTrue(result["temporary_absent"])
        self.assertEqual("effect-attempted-awaiting-observer", result["state"])
        self.assertEqual(self.before, self.checkpoint_path.read_bytes())

    def test_committed_source_cannot_touch_registered_production_target(self):
        self.assertEqual("unconfigured", owner.LOCAL_HOST_ID)
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)):
            with self.assertRaises(ValueError):
                owner.execute(
                    self.plan_raw, self.admission_raw, self.checkpoint_raw,
                    self.claim_raw, self.after,
                    operation_id="sa4-rehearsal-operation", effect_epoch=120)
        self.assertEqual(self.before, self.target_path.read_bytes())

    def test_changed_candidate_or_expired_admission_fails_before_write(self):
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), self.context():
            with self.assertRaises(ValueError):
                owner.execute(
                    self.plan_raw, self.admission_raw, self.checkpoint_raw,
                    self.claim_raw, b"changed candidate\n",
                    operation_id="sa4-rehearsal-operation", effect_epoch=120)
            expired = dict(self.admission); expired["expires_epoch"] = 119
            with self.assertRaises(ValueError):
                owner.execute(
                    self.plan_raw, contract.canonical(expired), self.checkpoint_raw,
                    self.claim_raw, self.after,
                    operation_id="sa4-rehearsal-operation", effect_epoch=120)
        self.assertEqual(self.before, self.target_path.read_bytes())

    def test_existing_temporary_or_checkpoint_drift_fails_before_write(self):
        Path(self.target.temporary_path).write_bytes(b"occupied")
        with self.assertRaises(ValueError): self.execute()
        Path(self.target.temporary_path).unlink()
        self.checkpoint_path.write_bytes(b"wrong")
        with self.assertRaises(ValueError): self.execute()
        self.assertEqual(self.before, self.target_path.read_bytes())


if __name__ == "__main__": unittest.main()
