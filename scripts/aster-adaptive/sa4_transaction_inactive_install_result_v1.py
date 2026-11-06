"""Validate the bounded result of the SA4 transaction inactive installation."""
from __future__ import annotations

import hashlib

import sa4_single_file_repair_contract_v1 as contract
import sa4_transaction_inactive_install_plan_v1 as install
from nlu_threshold_policy import decode_unique_json


HOST_BINDINGS = {
    "sa4_atomic_repair_owner_v1.py": "unconfigured",
    "sa4_atomic_rollback_owner_v1.py": "unconfigured",
    "sa4_independent_receipt_producer_v1.py": "unconfigured",
    "sa4_independent_rollback_receipt_producer_v1.py": "unconfigured",
}
HEALTH = ("lxc104", "lxc110", "lxc116", "aster-agent",
          "accepted-llama-sycl", "speech", "news-timers", "epub-baseline",
          "dispatcher", "doctor", "pvescheduler", "pvestatd")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def plan_sha256() -> str:
    return sha256(contract.canonical(install.plan()))


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "changes", "proxmox_parent_created",
              "isolated_imports", "host_bindings", "signer_fake_self_test",
              "private_key_accessed", "signer_invoked", "grant_touched",
              "checkpoint_owner_invoked", "target_touched", "service_actions",
              "production_health", "rollback_ready", "automatic_routing"}
    if (not isinstance(value, dict) or contract.canonical(value) != raw
            or set(value) != fields
            or value["schema"]
            != "aster-sa4-transaction-inactive-install-result.v1"
            or value["plan_sha256"] != plan_sha256()
            or value["proxmox_parent_created"] is not True
            or value["isolated_imports"] != [item.destination
                                             for item in install.CHANGES]
            or value["host_bindings"] != HOST_BINDINGS
            or value["signer_fake_self_test"] != "pass"
            or value["private_key_accessed"] is not False
            or value["signer_invoked"] is not False
            or value["grant_touched"] is not False
            or value["checkpoint_owner_invoked"] is not False
            or value["target_touched"] is not False
            or value["service_actions"] != []
            or value["production_health"] != {name: True for name in HEALTH}
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 inactive installation result changed")
    rows = value["changes"]
    if not isinstance(rows, list) or len(rows) != len(install.CHANGES):
        raise ValueError("SA4 inactive installation rows changed")
    for row, expected in zip(rows, install.CHANGES):
        fields = {"host_id", "destination", "before_state", "before_sha256",
                  "after_sha256", "owner", "group", "mode", "link_count",
                  "regular_file", "retained_predecessor"}
        replacement = expected.old_sha256 is not None
        if (not isinstance(row, dict) or set(row) != fields
                or row["host_id"] != expected.host_id
                or row["destination"] != expected.destination
                or row["before_state"]
                != ("present" if replacement else "absent")
                or row["before_sha256"] != expected.old_sha256
                or row["after_sha256"] != expected.new_sha256
                or row["owner"] != expected.owner
                or row["group"] != expected.group
                or row["mode"] != expected.mode
                or row["link_count"] != 1
                or row["regular_file"] is not True
                or row["retained_predecessor"] is not replacement):
            raise ValueError("SA4 inactive installation change changed")
    return {
        "schema": "aster-sa4-transaction-inactive-install-validation.v1",
        "result_sha256": sha256(raw), "changes_validated": len(rows),
        "inactive": True, "rollback_ready": True,
        "effect_authorized": False, "maximum_effects": 0,
        "automatic_routing": "off"}
