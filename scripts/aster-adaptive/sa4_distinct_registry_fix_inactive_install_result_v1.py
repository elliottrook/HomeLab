"""Strict validator for the inert SA4 distinct-registry correction result."""
from __future__ import annotations

import hashlib
import json


EXPECTED = {
    "/usr/local/libexec/aster-sa4/sa4_distinct_registry_bindings_v1.py":
        "c88640a32fb9a413afcd01e2dcdadcb4a5fc68f0bdd99a59e976aa5f83476330",
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v4.py":
        "9da52be5fba3d9a5c628e94a887f034944d6a75f31bf8dbb86471005ff5453e6",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v4.py":
        "ab2c67cd1640cbb60b3da89aadc9f90ee34132873295f8736f10ed0af3b79d0f",
}
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate(raw: bytes) -> dict[str, object]:
    value = json.loads(raw)
    fields = {
        "schema", "rows", "dependencies_exact", "v1_target_rejected",
        "complete_v2_binding", "nested_binding", "restored_v1",
        "runner_fail_before_input", "runner_exit_status",
        "transaction_state_absent", "runner_process_absent",
        "target_sha256", "lease_ready", "production_healthy",
        "service_actions", "repair_authorized", "automatic_routing",
    }
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"]
            != "aster-sa4-distinct-registry-fix-inactive-install-result.v1"
            or value["dependencies_exact"] is not True
            or value["v1_target_rejected"] is not True
            or value["complete_v2_binding"] is not True
            or value["nested_binding"] is not True
            or value["restored_v1"] is not True
            or value["runner_fail_before_input"] is not True
            or value["runner_exit_status"] != 1
            or value["transaction_state_absent"] is not True
            or value["runner_process_absent"] is not True
            or value["target_sha256"] != TARGET_SHA256
            or value["lease_ready"] is not True
            or value["production_healthy"] is not True
            or value["service_actions"] != []
            or value["repair_authorized"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 distinct registry correction result changed")
    rows = value["rows"]
    if (not isinstance(rows, list) or len(rows) != 3
            or {row.get("destination") for row in rows} != set(EXPECTED)):
        raise ValueError("SA4 distinct registry correction rows changed")
    for row in rows:
        if (set(row) != {"destination", "after_sha256", "owner", "group",
                         "mode", "regular_file", "link_count"}
                or row["after_sha256"] != EXPECTED[row["destination"]]
                or row["owner"] != "root" or row["group"] != "root"
                or row["mode"] != "0644" or row["regular_file"] is not True
                or row["link_count"] != 1):
            raise ValueError("SA4 distinct registry correction row changed")
    return {**value, "result_sha256": hashlib.sha256(raw).hexdigest(),
            "inactive": True}

