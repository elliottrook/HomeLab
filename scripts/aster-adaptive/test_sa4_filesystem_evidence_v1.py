import copy
import unittest

import sa4_filesystem_evidence_v1 as filesystem
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as target_registry
from test_sa4_single_file_repair_contract_v1 import plan


def measured_file(*, device=7, inode=11, mode="0644"):
    value = {
        "device": device, "inode": inode, "uid": 0, "gid": 0,
        "owner": "root", "group": "root", "mode": mode,
        "link_count": 1, "size": 25, "regular_file": True,
        "symlink": False, "bytes_sha256": "2" * 64,
        "metadata_sha256": "",
    }
    value["metadata_sha256"] = filesystem._metadata_digest(value)
    return value


def evidence(plan_raw):
    value = {
        "schema": "aster-sa4-filesystem-preflight-evidence.v1",
        "plan_sha256": filesystem.sha256(plan_raw),
        "target_id": "sa4-synthetic-fixture", "measurement_epoch": 100,
        "target_registration_sha256":
            target_registry.registration_sha256(
                target_registry.resolve_schema_fixture(
                    "sa4-synthetic-fixture")),
        "capture": {"host_id": "synthetic-host",
                    "path": "/synthetic/aster/example.conf",
                    "open_flags": list(filesystem.OPEN_FLAGS),
                    "path_lstat_type": "regular-file",
                    "fd_fstat_type": "regular-file",
                    "symlink_followed": False,
                    "descriptor_remained_open": True},
        "target": measured_file(),
        "checkpoint": {
            "path": "/synthetic/checkpoints/sa4-synthetic-single-file-v1.original",
            "distinct_path": True,
            "copy_method": "copy-from-open-target-fd-no-follow",
            "immutable": True,
            "file": measured_file(inode=12, mode="0600"),
        },
        "temporary": {"path": "/synthetic/aster/.example.conf.sa4-tmp",
                      "absent": True, "parent_device": 7,
                      "same_filesystem": True},
        "controls": {"shared_operation_lock": "held",
                     "lock_path": "/run/aster-sa4-operation.lock",
                     "lock_owner": "sa4-synthetic-single-file-v1",
                     "lock_regular_file": True, "lock_link_count": 1,
                     "emergency_stop": "armed",
                     "emergency_stop_owner": "sa4-synthetic-single-file-v1",
                     "automatic_retry": False},
        "postcheck_receipts": [{
            "id": name, "registered_check_sha256": digest,
            "state": "registered-not-run", "measurement_sha256": None,
        } for name, digest in filesystem.REGISTERED_POSTCHECKS.items()],
        "effects": 0, "authority": "none", "automatic_routing": "off",
    }
    return value


class SA4FilesystemEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.plan_raw = contract.canonical(plan())
        self.value = evidence(self.plan_raw)

    def validate(self, value):
        return filesystem.validate(self.plan_raw, contract.canonical(value))

    def test_exact_synthetic_evidence_validates_without_effect_authority(self):
        result = self.validate(self.value)
        self.assertTrue(result["filesystem_evidence_valid"])
        self.assertEqual(0, result["maximum_effects"])
        self.assertFalse(result["preflight_eligible"])
        self.assertEqual("none", result["authority"])

    def test_symlink_link_and_custody_drift_fail_closed(self):
        mutations = (
            lambda value: value["target"].update(symlink=True),
            lambda value: value["target"].update(link_count=2),
            lambda value: value["target"].update(uid=1000),
            lambda value: value["checkpoint"]["file"].update(mode="0644"),
        )
        for mutation in mutations:
            value = copy.deepcopy(self.value); mutation(value)
            with self.subTest(), self.assertRaises(ValueError): self.validate(value)

    def test_digest_inode_device_and_path_drift_fail_closed(self):
        mutations = (
            lambda value: value["target"].update(bytes_sha256="4" * 64),
            lambda value: value["target"].update(inode=0),
            lambda value: value["checkpoint"]["file"].update(inode=11),
            lambda value: value["checkpoint"]["file"].update(device=8),
            lambda value: value["capture"].update(path="/etc/shadow"),
            lambda value: value["checkpoint"].update(path="/synthetic/aster/example.conf"),
        )
        for mutation in mutations:
            value = copy.deepcopy(self.value); mutation(value)
            with self.subTest(), self.assertRaises(ValueError): self.validate(value)

    def test_nofollow_lock_emergency_and_temporary_drift_fail_closed(self):
        mutations = (
            lambda value: value["capture"].update(open_flags=["O_RDONLY"]),
            lambda value: value["capture"].update(symlink_followed=True),
            lambda value: value["controls"].update(shared_operation_lock="absent"),
            lambda value: value["controls"].update(lock_link_count=2),
            lambda value: value["controls"].update(emergency_stop="disarmed"),
            lambda value: value["temporary"].update(same_filesystem=False),
        )
        for mutation in mutations:
            value = copy.deepcopy(self.value); mutation(value)
            with self.subTest(), self.assertRaises(ValueError): self.validate(value)

    def test_postchecks_must_be_exact_registered_unrun_receipts(self):
        variants = []
        value = copy.deepcopy(self.value)
        value["postcheck_receipts"][0]["state"] = "passed"; variants.append(value)
        value = copy.deepcopy(self.value)
        value["postcheck_receipts"][1]["registered_check_sha256"] = "0" * 64
        variants.append(value)
        value = copy.deepcopy(self.value)
        value["postcheck_receipts"].reverse(); variants.append(value)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError): self.validate(value)

    def test_metadata_and_duplicate_key_drift_fail_closed(self):
        value = copy.deepcopy(self.value)
        value["target"]["metadata_sha256"] = "0" * 64
        with self.assertRaises(ValueError): self.validate(value)
        raw = contract.canonical(self.value).replace(
            b'"effects":0', b'"effects":0,"effects":0')
        with self.assertRaises(ValueError): filesystem.validate(self.plan_raw, raw)

    def test_target_registration_digest_drift_fails_closed(self):
        value = copy.deepcopy(self.value)
        value["target_registration_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            self.validate(value)


if __name__ == "__main__": unittest.main()
