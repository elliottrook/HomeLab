"""Strict validator for the inert SA4 v6 runner installation result."""
from __future__ import annotations

import hashlib
import json


DESTINATION = "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v6.py"
AFTER_SHA256 = (
    "a91d6a34ac251970a9d83452e085cbc4d0a51adaf065ec75d6879e122b38a397")
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate(raw: bytes) -> dict[str, object]:
    value = json.loads(raw)
    fields = {
        "schema", "row", "installed_v5_exact", "retained_v2_exact",
        "fresh_v3_state_absent", "runner_fail_before_input",
        "runner_exit_status", "target_sha256", "lease_ready",
        "production_healthy", "service_actions", "repair_authorized",
        "automatic_routing",
    }
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"]
            != "aster-sa4-fresh-path-runner-inactive-install-result.v1"
            or value["installed_v5_exact"] is not True
            or value["retained_v2_exact"] is not True
            or value["fresh_v3_state_absent"] is not True
            or value["runner_fail_before_input"] is not True
            or value["runner_exit_status"] != 1
            or value["target_sha256"] != TARGET_SHA256
            or value["lease_ready"] is not True
            or value["production_healthy"] is not True
            or value["service_actions"] != []
            or value["repair_authorized"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 v6 runner installation result changed")
    row = value["row"]
    if (not isinstance(row, dict)
            or set(row) != {"destination", "after_sha256", "owner", "group",
                            "mode", "regular_file", "link_count"}
            or row["destination"] != DESTINATION
            or row["after_sha256"] != AFTER_SHA256
            or row["owner"] != "root" or row["group"] != "root"
            or row["mode"] != "0644" or row["regular_file"] is not True
            or row["link_count"] != 1):
        raise ValueError("SA4 v6 runner installation row changed")
    return {**value, "result_sha256": hashlib.sha256(raw).hexdigest(),
            "inactive": True}
