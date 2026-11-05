import copy
import unittest

import sa4_single_file_repair_contract_v1 as repair


def plan():
    return {
        "schema": "aster-sa4-single-file-repair-plan.v1",
        "plan_id": "sa4-synthetic-single-file-v1",
        "candidate_release_sha256": "1" * 64,
        "repair_class": "single-file-configuration-drift",
        "target": {"host_id": "synthetic-host", "path": "/etc/aster/example.conf",
                   "type": "regular-file", "follow_symlinks": False,
                   "owner": "root", "group": "root", "mode": "0644"},
        "precondition": {"expected_sha256": "2" * 64,
                         "observed_mode": "0644",
                         "service_restart_required": False},
        "change": {"artifact_sha256": "3" * 64,
                   "method": "atomic-replace-no-follow",
                   "temporary_same_filesystem": True},
        "checkpoint": {"required": True, "immutable_copy_required": True,
                       "digest_required": True},
        "postchecks": list(repair.POSTCHECKS),
        "rollback": {"method": "atomic-restore-checkpoint-no-follow",
                     "trigger": "any-failed-or-uncertain-postcheck",
                     "verify_digest": True},
        "uncertainty": {"automatic_retry": False, "preserve_evidence": True,
                        "outcome": "stop-and-reconcile"},
        "exclusions": list(repair.EXCLUSIONS),
        "authority": "none", "effect_authorized": False,
        "automatic_routing": "off",
    }


def evidence(plan_raw):
    digest = repair.sha256(plan_raw)
    approval = {"schema": "aster-sa4-owner-approval.v1",
                "plan_sha256": digest, "owner_id": "jason",
                "decision": "approve-one-repair", "expires_epoch": 200,
                "scope": "exact-plan-only", "authority": "one-use-owner-approval"}
    grant = {"schema": "aster-sa4-ai-pam-grant.v1", "plan_sha256": digest,
             "grant_id": "synthetic-grant", "target_sha256": "2" * 64,
             "max_uses": 1, "expires_epoch": 150,
             "scope": "exact-target-atomic-replace", "authority": "one-use-ai-pam"}
    checkpoint = {"schema": "aster-sa4-checkpoint.v1", "plan_sha256": digest,
                  "target_before_sha256": "2" * 64,
                  "checkpoint_sha256": "4" * 64, "target_mode": "0644",
                  "owner": "root", "group": "root", "regular_file": True,
                  "link_count": 1, "authority": "none"}
    return tuple(repair.canonical(value) for value in (approval, grant, checkpoint))


class SA4SingleFileRepairContractTests(unittest.TestCase):
    def test_exact_plan_and_one_use_evidence_reach_preflight_only(self):
        raw = repair.canonical(plan())
        value = repair.admit(raw, *evidence(raw), now_epoch=100)
        self.assertTrue(value["preflight_eligible"])
        self.assertEqual(1, value["maximum_effects"])
        self.assertFalse(value["automatic_retry"])

    def test_plan_forbids_restart_symlink_and_unsafe_path(self):
        variants = []
        value = plan(); value["precondition"]["service_restart_required"] = True; variants.append(value)
        value = plan(); value["target"]["follow_symlinks"] = True; variants.append(value)
        value = plan(); value["target"]["path"] = "/etc/aster/../shadow"; variants.append(value)
        value = plan(); value["exclusions"].remove("credentials"); variants.append(value)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError):
                repair.validate_plan(repair.canonical(value))

    def test_expiry_reuse_and_binding_drift_fail_closed(self):
        raw = repair.canonical(plan()); approval, grant, checkpoint = evidence(raw)
        with self.assertRaises(ValueError):
            repair.admit(raw, approval, grant, checkpoint, now_epoch=150)
        changed = repair.decode_unique_json(grant); changed["max_uses"] = 2
        with self.assertRaises(ValueError):
            repair.admit(raw, approval, repair.canonical(changed), checkpoint, 100)
        changed = repair.decode_unique_json(checkpoint)
        changed["target_before_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            repair.admit(raw, approval, grant, repair.canonical(changed), 100)

    def test_unknown_and_duplicate_fields_fail_closed(self):
        value = plan(); value["command"] = "arbitrary"
        with self.assertRaises(ValueError): repair.validate_plan(repair.canonical(value))
        raw = repair.canonical(plan()).replace(
            b'"authority":"none"', b'"authority":"none","authority":"none"')
        with self.assertRaises(ValueError): repair.validate_plan(raw)


if __name__ == "__main__": unittest.main()
