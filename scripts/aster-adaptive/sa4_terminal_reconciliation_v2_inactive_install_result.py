"""Validate the inert four-file SA4 v2 terminal-chain installation."""
import hashlib

import sa4_single_file_repair_contract_v1 as contract
import sa4_terminal_reconciliation_v2_inactive_install_plan as install
from nlu_threshold_policy import decode_unique_json


ROW_FIELDS = {
    "destination", "after_sha256", "owner", "group", "mode",
    "link_count", "regular_file", "isolated_import"}
FIELDS = {
    "schema", "rows", "v1_dependencies_unchanged", "runner_invoked",
    "authority_touched", "ledger_touched", "target_touched",
    "runtime_state_absent", "service_actions", "production_healthy",
    "rollback_ready", "automatic_routing"}


def validate(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    if (not isinstance(value, dict) or set(value) != FIELDS
            or contract.canonical(value) != raw
            or value["schema"]
            != "aster-sa4-terminal-reconciliation-v2-inactive-install-result.v1"
            or not isinstance(value["rows"], list)
            or len(value["rows"]) != len(install.CHANGES)):
        raise ValueError("SA4 v2 inactive install result changed")
    for row, expected in zip(value["rows"], install.CHANGES):
        if (not isinstance(row, dict) or set(row) != ROW_FIELDS
                or row["destination"] != expected.destination
                or row["after_sha256"] != expected.after_sha256
                or (row["owner"], row["group"], row["mode"],
                    row["link_count"], row["regular_file"],
                    row["isolated_import"])
                != ("root", "root", "0644", 1, True, True)):
            raise ValueError("SA4 v2 inactive install row changed")
    if (value["v1_dependencies_unchanged"] is not True
            or value["runner_invoked"] is not False
            or value["authority_touched"] is not False
            or value["ledger_touched"] is not False
            or value["target_touched"] is not False
            or value["runtime_state_absent"] is not True
            or value["service_actions"] != []
            or value["production_healthy"] is not True
            or value["rollback_ready"] is not True
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 v2 inactive install boundary changed")
    return {
        "schema": "aster-sa4-terminal-reconciliation-v2-install-validation.v1",
        "result_sha256": hashlib.sha256(raw).hexdigest(),
        "inactive": True,
        "effect_authorized": False,
    }
