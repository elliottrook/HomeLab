"""Validate zero-effect SA4 filesystem and checkpoint preflight evidence.

This module consumes bounded measurements only.  It never opens, writes,
renames, locks, repairs, rolls back, or authorizes a target.
"""
from __future__ import annotations

import hashlib
import re

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as target_registry
from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
TARGET_PATH = "/synthetic/aster/example.conf"
CHECKPOINT_PREFIX = "/synthetic/checkpoints/"
TEMPORARY_PATH = "/synthetic/aster/.example.conf.sa4-tmp"
LOCK_PATH = "/run/aster-sa4-operation.lock"
OPEN_FLAGS = ["O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC"]
REGISTERED_POSTCHECKS = {
    "target-bytes": "1" * 64,
    "target-metadata": "2" * 64,
    "consumer-read-only-health": "3" * 64,
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hex(value: object) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _metadata_digest(value: dict[str, object]) -> str:
    fields = {
        "device": value["device"], "inode": value["inode"],
        "uid": value["uid"], "gid": value["gid"],
        "owner": value["owner"], "group": value["group"],
        "mode": value["mode"], "link_count": value["link_count"],
        "size": value["size"], "regular_file": value["regular_file"],
    }
    return sha256(contract.canonical(fields))


def _file_measurement(value: object, *, mode: str) -> bool:
    fields = {"device", "inode", "uid", "gid", "owner", "group", "mode",
              "link_count", "size", "regular_file", "symlink",
              "bytes_sha256", "metadata_sha256"}
    return (isinstance(value, dict) and set(value) == fields
            and type(value["device"]) is int and value["device"] > 0
            and type(value["inode"]) is int and value["inode"] > 0
            and value["uid"] == 0 and value["gid"] == 0
            and value["owner"] == "root" and value["group"] == "root"
            and value["mode"] == mode and value["link_count"] == 1
            and type(value["size"]) is int and value["size"] > 0
            and value["regular_file"] is True and value["symlink"] is False
            and _hex(value["bytes_sha256"])
            and value["metadata_sha256"] == _metadata_digest(value))


def validate(plan_raw: bytes, evidence_raw: bytes) -> dict[str, object]:
    """Validate exact synthetic preflight measurements and authorize nothing."""
    plan = contract.validate_plan(plan_raw)
    value = decode_unique_json(evidence_raw)
    fields = {"schema", "plan_sha256", "target_id",
              "target_registration_sha256", "measurement_epoch",
              "capture", "target", "checkpoint", "temporary", "controls",
              "postcheck_receipts", "effects", "authority",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-filesystem-preflight-evidence.v1"
            or value["plan_sha256"] != sha256(plan_raw)
            or value["target_id"] != "sa4-synthetic-fixture"
            or plan["target_id"] != value["target_id"]
            or value["target_registration_sha256"]
            != target_registry.registration_sha256(
                target_registry.resolve_schema_fixture(value["target_id"]))
            or type(value["measurement_epoch"]) is not int
            or value["measurement_epoch"] <= 0
            or value["effects"] != 0 or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 filesystem evidence envelope changed")

    capture = value["capture"]
    if (not isinstance(capture, dict) or set(capture) != {
            "host_id", "path", "open_flags", "path_lstat_type",
            "fd_fstat_type", "symlink_followed", "descriptor_remained_open"}
            or capture["host_id"] != "synthetic-host"
            or capture["path"] != TARGET_PATH
            or capture["open_flags"] != OPEN_FLAGS
            or capture["path_lstat_type"] != "regular-file"
            or capture["fd_fstat_type"] != "regular-file"
            or capture["symlink_followed"] is not False
            or capture["descriptor_remained_open"] is not True):
        raise ValueError("SA4 no-follow descriptor evidence changed")

    target = value["target"]
    if (not _file_measurement(target, mode="0644")
            or target["bytes_sha256"]
            != plan["precondition"]["expected_sha256"]):
        raise ValueError("SA4 target measurement changed")

    checkpoint = value["checkpoint"]
    if (not isinstance(checkpoint, dict) or set(checkpoint) != {
            "path", "distinct_path", "copy_method", "immutable", "file"}
            or checkpoint["path"]
            != CHECKPOINT_PREFIX + plan["plan_id"] + ".original"
            or checkpoint["path"] == capture["path"]
            or checkpoint["distinct_path"] is not True
            or checkpoint["copy_method"] != "copy-from-open-target-fd-no-follow"
            or checkpoint["immutable"] is not True
            or not _file_measurement(checkpoint["file"], mode="0600")
            or checkpoint["file"]["device"] != target["device"]
            or checkpoint["file"]["inode"] == target["inode"]
            or checkpoint["file"]["size"] != target["size"]
            or checkpoint["file"]["bytes_sha256"] != target["bytes_sha256"]):
        raise ValueError("SA4 checkpoint evidence changed")

    temporary = value["temporary"]
    if (not isinstance(temporary, dict) or set(temporary) != {
            "path", "absent", "parent_device", "same_filesystem"}
            or temporary["path"] != TEMPORARY_PATH
            or temporary["absent"] is not True
            or temporary["parent_device"] != target["device"]
            or temporary["same_filesystem"] is not True):
        raise ValueError("SA4 temporary-file boundary changed")

    controls = value["controls"]
    if (not isinstance(controls, dict) or set(controls) != {
            "shared_operation_lock", "lock_path", "lock_owner",
            "lock_regular_file", "lock_link_count", "emergency_stop",
            "emergency_stop_owner", "automatic_retry"}
            or controls["shared_operation_lock"] != "held"
            or controls["lock_path"] != LOCK_PATH
            or controls["lock_owner"] != plan["plan_id"]
            or controls["lock_regular_file"] is not True
            or controls["lock_link_count"] != 1
            or controls["emergency_stop"] != "armed"
            or controls["emergency_stop_owner"] != plan["plan_id"]
            or controls["automatic_retry"] is not False):
        raise ValueError("SA4 runtime controls changed")

    receipts = value["postcheck_receipts"]
    if (not isinstance(receipts, list) or len(receipts) != 3
            or [item.get("id") for item in receipts]
            != list(contract.POSTCHECKS)):
        raise ValueError("SA4 postcheck receipt set changed")
    for item in receipts:
        if (not isinstance(item, dict) or set(item) != {
                "id", "registered_check_sha256", "state", "measurement_sha256"}
                or item["registered_check_sha256"]
                != REGISTERED_POSTCHECKS[item["id"]]
                or item["state"] != "registered-not-run"
                or item["measurement_sha256"] is not None):
            raise ValueError("SA4 postcheck receipt changed")

    return {
        "schema": "aster-sa4-filesystem-evidence-validation.v1",
        "plan_sha256": sha256(plan_raw),
        "evidence_sha256": sha256(evidence_raw),
        "target_registration_sha256": value["target_registration_sha256"],
        "target_bytes_sha256": target["bytes_sha256"],
        "checkpoint_bytes_sha256": checkpoint["file"]["bytes_sha256"],
        "no_follow_descriptor_proven": True,
        "checkpoint_proven": True,
        "shared_lock_proven": True,
        "emergency_stop_proven": True,
        "postchecks_registered_not_run": 3,
        "filesystem_evidence_valid": True,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "authority": "none",
        "automatic_routing": "off",
    }
