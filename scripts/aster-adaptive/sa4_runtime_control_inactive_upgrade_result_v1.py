"""Validate the inactive SA4 runtime-control correction result."""
from __future__ import annotations

import hashlib

import sa4_runtime_control_inactive_upgrade_plan_v1 as upgrade
import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json


PLAN_SHA256 = "83bdbf6f7021392946ed33dc12f0f3190b4a5f9010934b7e4ffa9e2b6c502ca8"


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "changes", "isolated_imports",
              "operation_lock_absent", "emergency_stop_absent",
              "root_owner_invoked", "authority_touched", "target_touched",
              "service_actions", "production_healthy", "rollback_ready",
              "automatic_routing"}
    if (not isinstance(value, dict) or contract.canonical(value) != raw
            or set(value) != fields
            or value["schema"]
            != "aster-sa4-runtime-control-inactive-upgrade-result.v1"
            or value["plan_sha256"] != PLAN_SHA256
            or value["isolated_imports"]
            != [item.destination for item in upgrade.CHANGES]
            or value["operation_lock_absent"] is not True
            or value["emergency_stop_absent"] is not True
            or value["root_owner_invoked"] is not False
            or value["authority_touched"] is not False
            or value["target_touched"] is not False
            or value["service_actions"] != []
            or value["production_healthy"] is not True
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 runtime-control upgrade result changed")
    rows = value["changes"]
    if not isinstance(rows, list) or len(rows) != 2:
        raise ValueError("SA4 runtime-control upgrade rows changed")
    for row, expected in zip(rows, upgrade.CHANGES):
        if (not isinstance(row, dict) or set(row) != {
                "destination", "before_sha256", "after_sha256", "owner",
                "group", "mode", "link_count", "regular_file",
                "retained_predecessor"}
                or row["destination"] != expected.destination
                or row["before_sha256"] != expected.before_sha256
                or row["after_sha256"] != expected.after_sha256
                or row["owner"] != "root" or row["group"] != "root"
                or row["mode"] != "0644" or row["link_count"] != 1
                or row["regular_file"] is not True
                or row["retained_predecessor"]
                is not (expected.before_sha256 is not None)):
            raise ValueError("SA4 runtime-control upgrade row changed")
    return {"schema": "aster-sa4-runtime-control-upgrade-validation.v1",
            "result_sha256": hashlib.sha256(raw).hexdigest(),
            "changes_validated": 2, "inactive": True,
            "effect_authorized": False, "maximum_effects": 0,
            "rollback_ready": True, "automatic_routing": "off"}
