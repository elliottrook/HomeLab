"""Strict validator for the inert SA4 postcheck-lineage installation."""
from __future__ import annotations

import hashlib
import json


EXPECTED = {
    "/usr/local/libexec/aster-sa4/sa4_canary_v2_target_bytes_check_v1.py":
        "74ee440c6f7617c726c634fd79ccfaf0e5d3df77cba4ba1b0aafcb78a64b0e06",
    "/usr/local/libexec/aster-sa4/sa4_canary_v2_target_metadata_check_v1.py":
        "23fb5ac611c0e7e04ab672c0ab17eb86c92e4a9c9e334b6879d56066ae395fea",
    "/usr/local/libexec/aster-sa4/sa4_canary_v2_consumer_health_check_v1.py":
        "4b792ff436a605a699dac3b73d4eb319b22ca4302ccf83ad3904379ba7fb4b28",
    "/usr/local/libexec/aster-sa4/sa4_target_registry_v3.py":
        "35e7f680a10d4936ba246cd51e844d9cacbf47c6bda018ab27a88295ad304857",
    "/usr/local/libexec/aster-sa4/sa4_distinct_postcheck_receipt_producer_v1.py":
        "96fa810011429f8da9fc1208a60471d745c452ed1ea9186552abf1ac4edeab29",
    "/usr/local/libexec/aster-sa4/sa4_distinct_registry_bindings_v2.py":
        "b40a9b657cb3f1b9087d5621fb96e11735bb578c06bbfdea3fd342cdd8baa370",
    "/usr/local/libexec/aster-sa4/sa4_root_transaction_owner_v6.py":
        "74ebd4e13137646dfff7a608bb3a9bb77050639968eaac321a15e7fb126dbd6f",
    "/usr/local/libexec/aster-sa4/sa4_fixed_transaction_runner_v7.py":
        "8b3f030b06d2cb677a5a106ee3a4a8f4ca27360ad19403bd927dc672dd7c322d",
}
TARGET_SHA256 = (
    "a9831e6295abd632ad0646b38a253fce71c29f76850d918d1761685c40824da0")


def validate(raw: bytes) -> dict[str, object]:
    value = json.loads(raw)
    fields = {"schema", "rows", "v2_postchecks_pass", "registry_pins_exact",
              "observer_binding_complete", "retained_attempts_exact",
              "fresh_v4_state_absent", "runner_fail_before_input",
              "runner_exit_status", "target_sha256", "lease_ready",
              "production_healthy", "service_actions", "repair_authorized",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"]
            != "aster-sa4-postcheck-lineage-inactive-install-result.v1"
            or any(value[name] is not True for name in (
                "v2_postchecks_pass", "registry_pins_exact",
                "observer_binding_complete", "retained_attempts_exact",
                "fresh_v4_state_absent", "runner_fail_before_input",
                "lease_ready", "production_healthy"))
            or value["runner_exit_status"] != 1
            or value["target_sha256"] != TARGET_SHA256
            or value["service_actions"] != []
            or value["repair_authorized"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 postcheck-lineage installation result changed")
    rows = value["rows"]
    if (not isinstance(rows, list) or len(rows) != 8
            or {row.get("destination") for row in rows} != set(EXPECTED)):
        raise ValueError("SA4 postcheck-lineage installation rows changed")
    for row in rows:
        if (set(row) != {"destination", "after_sha256", "owner", "group",
                         "mode", "regular_file", "link_count"}
                or row["after_sha256"] != EXPECTED[row["destination"]]
                or (row["owner"], row["group"], row["mode"],
                    row["regular_file"], row["link_count"])
                != ("root", "root", "0644", True, 1)):
            raise ValueError("SA4 postcheck-lineage installation row changed")
    return {**value, "result_sha256": hashlib.sha256(raw).hexdigest(),
            "inactive": True}
