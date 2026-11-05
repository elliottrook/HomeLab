from dataclasses import replace
import hashlib
import inspect
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sa4_inactive_measurement_owner_v1 as owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from test_sa4_single_file_repair_contract_v1 import plan


class SA4InactiveMeasurementOwnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.target_path = root / "example.conf"
        self.target_path.write_bytes(b"synthetic measurement bytes\n")
        os.chmod(self.target_path, 0o644)
        fixture = registry.SCHEMA_FIXTURES[0]
        self.target = replace(
            fixture, host_id="sa4-test-host", path=str(self.target_path),
            checkpoint_parent=str(root / "checkpoints"),
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

    def measure(self):
        with patch.object(registry, "SCHEMA_FIXTURES", (self.target,)), \
                patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
                patch.object(owner, "EXPECTED_UID", os.geteuid()), \
                patch.object(owner, "EXPECTED_GID", os.getegid()), \
                patch.object(owner, "LOCAL_HOST_ID", self.target.host_id):
            return owner.measure(self.plan_raw, measurement_epoch=100)

    def test_committed_source_has_no_measurable_production_target(self):
        self.assertEqual(1, len(registry.PRODUCTION_TARGETS))
        with self.assertRaises(ValueError):
            owner.measure(contract.canonical(plan()), measurement_epoch=100)

    def test_exact_read_only_descriptor_measurement_authorizes_nothing(self):
        result = self.measure()
        self.assertTrue(result["path_descriptor_stable"])
        self.assertFalse(result["checkpoint_created"])
        self.assertFalse(result["grant_claimed"])
        self.assertEqual(0, result["repair_effects"])
        self.assertFalse(result["preflight_eligible"])
        self.assertEqual(self.target_path.read_bytes(),
                         b"synthetic measurement bytes\n")

    def test_measurement_api_accepts_no_path_registry_or_host_override(self):
        self.assertEqual(["plan_raw", "measurement_epoch"], list(
            inspect.signature(owner.measure).parameters))

    def test_symlink_hardlink_mode_and_bytes_drift_fail_closed(self):
        outside = Path(self.temporary.name) / "outside"
        outside.write_bytes(self.target_path.read_bytes())
        original = self.target_path
        original.unlink(); original.symlink_to(outside)
        with self.assertRaises(OSError):
            self.measure()
        original.unlink(); original.write_bytes(outside.read_bytes())
        os.chmod(original, 0o644)
        linked = Path(self.temporary.name) / "linked"
        os.link(original, linked)
        with self.assertRaises(ValueError):
            self.measure()
        linked.unlink(); os.chmod(original, 0o600)
        with self.assertRaises(ValueError):
            self.measure()
        os.chmod(original, 0o644); original.write_bytes(b"changed\n")
        with self.assertRaises(ValueError):
            self.measure()


if __name__ == "__main__":
    unittest.main()
