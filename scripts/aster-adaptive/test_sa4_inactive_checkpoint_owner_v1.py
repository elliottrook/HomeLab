from dataclasses import replace
import hashlib
import inspect
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4InactiveCheckpointOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.target_path = root / "example.conf"
        self.target_path.write_bytes(b"synthetic checkpoint bytes\n")
        os.chmod(self.target_path, 0o644)
        self.checkpoints = root / "checkpoints"
        self.checkpoints.mkdir(mode=0o700)
        fixture = registry.SCHEMA_FIXTURES[0]
        self.target = replace(
            fixture, host_id="sa4-test-host", path=str(self.target_path),
            checkpoint_parent=str(self.checkpoints),
            temporary_path=str(root / ".example.conf.sa4-tmp"))
        value = plan()
        value["target"] = {
            "host_id": self.target.host_id, "path": self.target.path,
            "type": "regular-file", "follow_symlinks": False,
            "owner": "root", "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = hashlib.sha256(
            self.target_path.read_bytes()).hexdigest()
        self.plan_raw = contract.canonical(value)

    def tearDown(self):
        self.temporary.cleanup()

    def context(self):
        return patch.multiple(
            registry, SCHEMA_FIXTURES=(self.target,),
            PRODUCTION_TARGETS=(self.target,))

    def measure(self):
        with self.context(), \
                patch.object(measurement_owner, "EXPECTED_UID", os.geteuid()), \
                patch.object(measurement_owner, "EXPECTED_GID", os.getegid()), \
                patch.object(measurement_owner, "LOCAL_HOST_ID", self.target.host_id):
            return measurement_owner.measure(self.plan_raw, measurement_epoch=100)

    def create(self, measurement):
        with self.context(), \
                patch.object(checkpoint_owner, "EXPECTED_UID", os.geteuid()), \
                patch.object(checkpoint_owner, "EXPECTED_GID", os.getegid()), \
                patch.object(checkpoint_owner, "LOCAL_HOST_ID", self.target.host_id):
            return checkpoint_owner.create(
                self.plan_raw, contract.canonical(measurement),
                checkpoint_epoch=101)

    def test_committed_source_cannot_create_live_checkpoint(self):
        self.assertEqual((), registry.PRODUCTION_TARGETS)
        with self.assertRaises(ValueError):
            checkpoint_owner.create(
                contract.canonical(plan()), b"{}\n", checkpoint_epoch=101)

    def test_exact_checkpoint_is_exclusive_and_target_unchanged(self):
        before = self.target_path.read_bytes()
        result = self.create(self.measure())
        path = Path(result["checkpoint_path"])
        self.assertEqual(before, path.read_bytes())
        self.assertEqual(before, self.target_path.read_bytes())
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertEqual(1, path.stat().st_nlink)
        self.assertFalse(result["grant_claimed"])
        self.assertEqual(0, result["repair_effects"])
        self.assertFalse(result["preflight_eligible"])
        with self.assertRaises(ValueError):
            self.create(self.measure())

    def test_api_accepts_no_path_host_registry_or_checkpoint_override(self):
        self.assertEqual(
            ["plan_raw", "measurement_raw", "checkpoint_epoch"],
            list(inspect.signature(checkpoint_owner.create).parameters))

    def test_stale_or_changed_measurement_fails_without_checkpoint(self):
        measured = self.measure()
        self.target_path.write_bytes(b"changed after measurement\n")
        os.chmod(self.target_path, 0o644)
        with self.assertRaises(ValueError):
            self.create(measured)
        self.assertFalse(any(self.checkpoints.glob("*.original")))
        self.target_path.write_bytes(b"synthetic checkpoint bytes\n")
        os.chmod(self.target_path, 0o644)
        measured = self.measure(); measured["measurement_epoch"] = -1
        with self.assertRaises(ValueError):
            self.create(measured)

    def test_checkpoint_directory_and_measurement_drift_fail_closed(self):
        measured = self.measure()
        os.chmod(self.checkpoints, 0o755)
        with self.assertRaises(ValueError):
            self.create(measured)
        os.chmod(self.checkpoints, 0o700)
        measured["checkpoint_created"] = True
        with self.assertRaises(ValueError):
            self.create(measured)


if __name__ == "__main__":
    unittest.main()
