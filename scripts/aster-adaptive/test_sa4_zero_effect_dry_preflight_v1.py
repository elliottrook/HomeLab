from dataclasses import replace
import copy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
import sa4_zero_effect_dry_preflight_v1 as preflight
from test_sa4_single_file_repair_contract_v1 import plan


ROOT = Path(__file__).parents[2]
INSTALL_RAW = (ROOT / "docs/projects/AI Projects/evidence/"
               "SA4-transaction-inactive-install-result-2026-11-05.json").read_bytes()


class SA4ZeroEffectDryPreflightTests(unittest.TestCase):
    def setUp(self):
        base = registry.PRODUCTION_TARGETS[0]
        self.target = replace(base, host_id="dry-preflight-test-host",
                              path="/synthetic/dry-preflight.json")
        value = plan(); value["target_id"] = self.target.target_id
        value["target"] = {"host_id": self.target.host_id,
                           "path": self.target.path, "type": "regular-file",
                           "follow_symlinks": False, "owner": "root",
                           "group": "root", "mode": "0644"}
        value["precondition"]["expected_sha256"] = "1" * 64
        self.plan_raw = contract.canonical(value)
        snapshot = {"device": 7, "inode": 8, "uid": 0, "gid": 0,
                    "mode": "0644", "link_count": 1, "size": 25,
                    "mtime_ns": 9, "ctime_ns": 10, "regular_file": True,
                    "bytes_sha256": "1" * 64, "metadata_sha256": "2" * 64}
        self.measurement_raw = contract.canonical({
            "schema": "aster-sa4-inactive-target-measurement.v1",
            "plan_sha256": preflight.sha256(self.plan_raw),
            "target_id": self.target.target_id,
            "target_registration_sha256": registry.registration_sha256(self.target),
            "measurement_epoch": 100, "host_id": self.target.host_id,
            "path": self.target.path,
            "open_flags": ["O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC"],
            "path_descriptor_stable": True, "target_snapshot": snapshot,
            "checkpoint_created": False, "grant_claimed": False,
            "repair_effects": 0, "preflight_eligible": False,
            "authority": "none", "automatic_retry": False})
        self.ceremony_raw = contract.canonical({
            "plan_sha256": preflight.sha256(self.plan_raw),
            "effect_authorized": False, "grant_consumed": False,
            "maximum_effects": 0, "preflight_eligible": False,
            "automatic_routing": "off"})
        self.runtime = {
            "schema": "aster-sa4-zero-effect-runtime-state.v1",
            "plan_sha256": preflight.sha256(self.plan_raw),
            "install_result_sha256": preflight.INSTALL_RESULT_SHA256,
            "measurement_sha256": preflight.sha256(self.measurement_raw),
            "observed_epoch": 120, "target_sha256": "1" * 64,
            "repair_checkpoint_absent": True, "temporary_absent": True,
            "ledger_absent": True, "operation_process_absent": True,
            "host_bindings": dict(preflight.HOST_BINDINGS),
            "signer_invoked": False, "private_key_accessed": False,
            "production_health": {name: True for name in preflight.HEALTH},
            "automatic_routing": "off"}

    def compose(self, runtime=None):
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)):
            return preflight.compose(
                self.plan_raw, INSTALL_RAW, self.ceremony_raw,
                self.measurement_raw,
                contract.canonical(self.runtime if runtime is None else runtime),
                now_epoch=120)

    def test_exact_fresh_state_completes_only_zero_effect_dry_preflight(self):
        result = self.compose()
        self.assertTrue(result["dry_preflight_complete"])
        self.assertFalse(result["preflight_eligible"])
        self.assertFalse(result["effect_authorized"])
        self.assertEqual(0, result["maximum_effects"])

    def test_any_state_or_health_presence_fails_closed(self):
        for field in ("repair_checkpoint_absent", "temporary_absent",
                      "ledger_absent", "operation_process_absent"):
            changed = copy.deepcopy(self.runtime); changed[field] = False
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.compose(changed)
        changed = copy.deepcopy(self.runtime)
        changed["production_health"]["aster-agent"] = False
        with self.assertRaises(ValueError): self.compose(changed)

    def test_measurement_install_or_ceremony_lineage_cannot_drift(self):
        changed = bytearray(INSTALL_RAW); changed[-2] ^= 1
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             self.assertRaises(ValueError):
            preflight.compose(
                self.plan_raw, bytes(changed), self.ceremony_raw,
                self.measurement_raw, contract.canonical(self.runtime),
                now_epoch=120)
        ceremony = contract.canonical({
            "plan_sha256": preflight.sha256(self.plan_raw),
            "effect_authorized": True, "grant_consumed": False,
            "maximum_effects": 0, "preflight_eligible": False,
            "automatic_routing": "off"})
        with patch.object(registry, "PRODUCTION_TARGETS", (self.target,)), \
             self.assertRaises(ValueError):
            preflight.compose(
                self.plan_raw, INSTALL_RAW, ceremony, self.measurement_raw,
                contract.canonical(self.runtime), now_epoch=120)


if __name__ == "__main__":
    unittest.main()
