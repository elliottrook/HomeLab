"""Validate the bounded result of the SA4 root-owner inactive upgrade."""
from __future__ import annotations

import hashlib

import sa4_root_owner_inactive_upgrade_plan_v1 as upgrade
import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json


PLAN_SHA256 = "f7ab264cd40f6639b23c59ab68e36e1c92cea2032bd72f9645f6831e800c9943"
HEALTH = ("lxc104", "lxc110", "lxc116", "aster-agent",
          "accepted-llama-sycl", "speech", "news-timers", "epub-baseline",
          "dispatcher", "doctor", "pvescheduler", "pvestatd")
HOST_BINDINGS = {
    "sa4_atomic_repair_owner_v1.py": "unconfigured",
    "sa4_atomic_rollback_owner_v1.py": "unconfigured",
    "sa4_independent_receipt_producer_v1.py": "unconfigured",
    "sa4_independent_rollback_receipt_producer_v1.py": "unconfigured"}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "changes", "isolated_imports",
              "host_bindings", "private_key_accessed", "signer_invoked",
              "authority_touched", "ledger_touched", "checkpoint_touched",
              "target_touched", "root_owner_invoked", "service_actions",
              "production_health", "rollback_ready", "automatic_routing"}
    if (not isinstance(value, dict) or contract.canonical(value) != raw
            or set(value) != fields
            or value["schema"]
            != "aster-sa4-root-owner-inactive-upgrade-result.v1"
            or value["plan_sha256"] != PLAN_SHA256
            or value["isolated_imports"]
            != [item.destination for item in upgrade.CHANGES]
            or value["host_bindings"] != HOST_BINDINGS
            or any(value[name] is not False for name in (
                "private_key_accessed", "signer_invoked", "authority_touched",
                "ledger_touched", "checkpoint_touched", "target_touched",
                "root_owner_invoked"))
            or value["service_actions"] != []
            or value["production_health"] != {name: True for name in HEALTH}
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 root-owner inactive upgrade result changed")
    rows = value["changes"]
    if not isinstance(rows, list) or len(rows) != len(upgrade.CHANGES):
        raise ValueError("SA4 root-owner upgrade rows changed")
    for row, expected in zip(rows, upgrade.CHANGES):
        row_fields = {"destination", "before_sha256", "after_sha256",
                      "owner", "group", "mode", "link_count",
                      "regular_file", "retained_predecessor"}
        if (not isinstance(row, dict) or set(row) != row_fields
                or row["destination"] != expected.destination
                or row["before_sha256"] != expected.before_sha256
                or row["after_sha256"] != expected.after_sha256
                or row["owner"] != "root" or row["group"] != "root"
                or row["mode"] != "0644" or row["link_count"] != 1
                or row["regular_file"] is not True
                or row["retained_predecessor"]
                is not (expected.before_sha256 is not None)):
            raise ValueError("SA4 root-owner upgrade change changed")
    return {"schema": "aster-sa4-root-owner-inactive-upgrade-validation.v1",
            "result_sha256": sha256(raw), "changes_validated": len(rows),
            "inactive": True, "rollback_ready": True,
            "effect_authorized": False, "maximum_effects": 0,
            "automatic_routing": "off"}
