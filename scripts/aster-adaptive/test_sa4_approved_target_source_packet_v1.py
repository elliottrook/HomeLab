import copy
import hashlib
from pathlib import Path
import unittest

import sa4_canary_consumer_health_check_v1 as consumer
import sa4_canary_rollback_check_v1 as rollback
import sa4_canary_target_bytes_check_v1 as byte_check
import sa4_canary_target_metadata_check_v1 as metadata_check
import sa4_authenticated_authority_v1 as authority
import sa4_independent_postcheck_receipt_v1 as observer
import sa4_key_custody_slots_v1 as custody
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


HEALTHY = contract.canonical({
    "adapter": "sa4-canary", "schema": "aster-sa4-canary-adapter.v1",
    "state": "healthy"})
DRIFTED = contract.canonical({
    "adapter": "sa4-canary", "schema": "aster-sa4-canary-adapter.v1",
    "state": "drifted"})


class SA4ApprovedTargetSourcePacketTests(unittest.TestCase):
    def test_fixed_checks_accept_only_exact_expected_evidence(self):
        self.assertEqual("pass", byte_check.check(HEALTHY)["state"])
        self.assertEqual("pass", consumer.check(HEALTHY)["state"])
        self.assertEqual("pass", rollback.check(DRIFTED)["state"])
        metadata = {"device": 1, "inode": 2, "uid": 0, "gid": 0,
                    "mode": "0644", "link_count": 1, "size": len(HEALTHY),
                    "regular_file": True, "symlink": False,
                    "bytes_sha256": byte_check.EXPECTED_SHA256}
        self.assertEqual("pass", metadata_check.check(metadata)["state"])
        for module, raw in ((byte_check, DRIFTED), (consumer, DRIFTED),
                            (rollback, HEALTHY)):
            with self.subTest(module=module.__name__), self.assertRaises(ValueError):
                module.check(raw)
        changed = copy.deepcopy(metadata); changed["link_count"] = 2
        with self.assertRaises(ValueError):
            metadata_check.check(changed)

    def test_compiled_target_is_source_only_and_exact(self):
        target = registry.resolve_production("sa4-lxc104-canary-adapter-v1")
        self.assertEqual("lxc104", target.host_id)
        self.assertEqual("/var/lib/aster/sa4/canary-adapter.json", target.path)
        self.assertFalse(target.service_restart_required)
        self.assertFalse(target.automatic_retry)
        self.assertEqual(4096, target.maximum_bytes)
        root = Path(__file__).parent
        programs = (
            "sa4_canary_target_bytes_check_v1.py",
            "sa4_canary_target_metadata_check_v1.py",
            "sa4_canary_consumer_health_check_v1.py")
        self.assertEqual(target.postcheck_program_sha256, tuple(
            hashlib.sha256((root / name).read_bytes()).hexdigest()
            for name in programs))
        self.assertEqual(target.rollback_program_sha256, hashlib.sha256(
            (root / "sa4_canary_rollback_check_v1.py").read_bytes()).hexdigest())
        acceptance = root.parents[1] / "docs/projects/AI Projects/evidence/SA4-first-target-owner-acceptance-2026-11-05.json"
        self.assertEqual(target.owner_review_sha256,
                         hashlib.sha256(acceptance.read_bytes()).hexdigest())

    def test_production_plan_resolves_only_the_compiled_target(self):
        target = registry.resolve_production("sa4-lxc104-canary-adapter-v1")
        value = {
            "schema": "aster-sa4-single-file-repair-plan.v1",
            "plan_id": "sa4-canary-first-repair-v1",
            "target_id": target.target_id,
            "candidate_release_sha256": "a" * 64,
            "repair_class": "single-file-configuration-drift",
            "target": {"host_id": target.host_id, "path": target.path,
                       "type": "regular-file", "follow_symlinks": False,
                       "owner": "root", "group": "root", "mode": "0644"},
            "precondition": {"expected_sha256": rollback.EXPECTED_SHA256,
                             "observed_mode": "0644",
                             "service_restart_required": False},
            "change": {"artifact_sha256": byte_check.EXPECTED_SHA256,
                       "method": "atomic-replace-no-follow",
                       "temporary_same_filesystem": True},
            "checkpoint": {"required": True,
                           "immutable_copy_required": True,
                           "digest_required": True},
            "postchecks": list(contract.POSTCHECKS),
            "rollback": {"method": "atomic-restore-checkpoint-no-follow",
                         "trigger": "any-failed-or-uncertain-postcheck",
                         "verify_digest": True},
            "uncertainty": {"automatic_retry": False,
                            "preserve_evidence": True,
                            "outcome": "stop-and-reconcile"},
            "exclusions": list(contract.EXCLUSIONS), "authority": "none",
            "effect_authorized": False, "automatic_routing": "off"}
        self.assertEqual(target.target_id,
                         contract.validate_plan(contract.canonical(value))["target_id"])

    def test_key_slots_are_empty_separate_and_not_runtime_nominable(self):
        custody.validate()
        self.assertEqual(3, len(custody.SLOTS))
        self.assertEqual(3, len({slot.custody_domain for slot in custody.SLOTS}))
        self.assertTrue(all(slot.public_key_sha256 is None for slot in custody.SLOTS))
        self.assertTrue(all(not slot.runtime_key_nomination for slot in custody.SLOTS))
        self.assertEqual(("owner-approval", "ai-pam-grant"), tuple(
            slot.role for slot in authority.AUTHORITY_KEY_SLOTS))
        self.assertEqual("independent-observer", observer.OBSERVER_KEY_SLOT.role)
        self.assertEqual({"owner-approval": {}, "ai-pam-grant": {}},
                         authority.TRUSTED_KEYS)
        self.assertEqual({}, observer.TRUSTED_OBSERVERS)


if __name__ == "__main__":
    unittest.main()
