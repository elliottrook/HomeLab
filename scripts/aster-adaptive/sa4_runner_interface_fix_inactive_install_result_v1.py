"""Strict validator for the inert SA4 v5 interface installation result."""
from __future__ import annotations

import hashlib
import json


EXPECTED = {
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v5.py":
        "a4fd70730a9e752e12430c1ab2179eb0c876118ab839c946850dd3377df6167a",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v5.py":
        "1071e4aa857e9ad1b6f3fa53de2ea22500919f278906f9b997f2ace1579c7b6f",
}
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate(raw: bytes) -> dict[str, object]:
    value = json.loads(raw)
    fields = {
        "schema", "rows", "predecessor_exact",
        "retained_failed_attempt_exact", "staging_recovery_completed",
        "fixed_target_interface", "runner_fail_before_input",
        "runner_exit_status", "ledger_absent", "runtime_controls_absent",
        "target_sha256", "lease_ready", "production_healthy",
        "service_actions", "repair_authorized", "automatic_routing",
    }
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"]
            != "aster-sa4-runner-interface-fix-inactive-install-result.v1"
            or value["predecessor_exact"] is not True
            or value["retained_failed_attempt_exact"] is not True
            or value["staging_recovery_completed"] is not True
            or value["fixed_target_interface"] is not True
            or value["runner_fail_before_input"] is not True
            or value["runner_exit_status"] != 1
            or value["ledger_absent"] is not True
            or value["runtime_controls_absent"] is not True
            or value["target_sha256"] != TARGET_SHA256
            or value["lease_ready"] is not True
            or value["production_healthy"] is not True
            or value["service_actions"] != []
            or value["repair_authorized"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 v5 interface installation result changed")
    rows = value["rows"]
    if (not isinstance(rows, list) or len(rows) != 2
            or {row.get("destination") for row in rows} != set(EXPECTED)):
        raise ValueError("SA4 v5 interface installation rows changed")
    for row in rows:
        if (set(row) != {"destination", "after_sha256", "owner", "group",
                         "mode", "regular_file", "link_count"}
                or row["after_sha256"] != EXPECTED[row["destination"]]
                or row["owner"] != "root" or row["group"] != "root"
                or row["mode"] != "0644" or row["regular_file"] is not True
                or row["link_count"] != 1):
            raise ValueError("SA4 v5 interface installation row changed")
    return {**value, "result_sha256": hashlib.sha256(raw).hexdigest(),
            "inactive": True}
