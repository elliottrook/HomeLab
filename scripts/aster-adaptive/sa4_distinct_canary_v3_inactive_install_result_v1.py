"""Validate the inactive distinct-canary v3 transaction installation."""
from __future__ import annotations

import hashlib

import sa4_distinct_canary_v3_inactive_install_plan_v1 as install
import sa4_single_file_repair_contract_v1 as contract
from nlu_threshold_policy import decode_unique_json


ROW_FIELDS = {
    "destination", "after_sha256", "owner", "group", "mode",
    "link_count", "regular_file",
}
FIELDS = {
    "schema", "rows", "dependencies_exact", "isolated_imports",
    "v1_target_rejected", "v2_target_resolved", "runner_invoked",
    "transaction_state_absent", "target_sha256", "service_actions",
    "production_healthy", "rollback_ready", "automatic_routing",
}


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if (not isinstance(value, dict) or set(value) != FIELDS
            or contract.canonical(value) != raw
            or value["schema"]
            != "aster-sa4-distinct-canary-v3-inactive-install-result.v1"
            or not isinstance(value["rows"], list)
            or len(value["rows"]) != len(install.CHANGES)):
        raise ValueError("SA4 distinct-canary v3 install result changed")
    for row, expected in zip(value["rows"], install.CHANGES):
        if (not isinstance(row, dict) or set(row) != ROW_FIELDS
                or row["destination"] != expected.destination
                or row["after_sha256"] != expected.after_sha256
                or (row["owner"], row["group"], row["mode"],
                    row["link_count"], row["regular_file"])
                != ("root", "root", "0644", 1, True)):
            raise ValueError("SA4 distinct-canary v3 install row changed")
    if (value["dependencies_exact"] is not True
            or value["isolated_imports"] is not True
            or value["v1_target_rejected"] is not True
            or value["v2_target_resolved"] is not True
            or value["runner_invoked"] is not False
            or value["transaction_state_absent"] is not True
            or value["target_sha256"] != install.TARGET_SHA256
            or value["service_actions"] != []
            or value["production_healthy"] is not True
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 distinct-canary v3 inactive boundary changed")
    return {
        "schema": "aster-sa4-distinct-canary-v3-install-validation.v1",
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "inactive": True,
        "repair_authorized": False,
    }

