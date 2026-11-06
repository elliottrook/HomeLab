"""Compose a fresh live SA4 dry preflight that can never admit an effect."""
from __future__ import annotations

import hashlib

import sa4_inactive_checkpoint_owner_v1 as checkpoint_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
import sa4_transaction_inactive_install_result_v1 as installation
from nlu_threshold_policy import decode_unique_json


INSTALL_RESULT_SHA256 = \
    "d0e2fbcddc02aa5636fcb7f267826e31040885c0435756eb4e770c5e97df0c9d"
HOST_BINDINGS = dict(installation.HOST_BINDINGS)
HEALTH = installation.HEALTH


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def compose(plan_raw: bytes, install_result_raw: bytes,
            ceremony_raw: bytes, measurement_raw: bytes,
            runtime_raw: bytes, *, now_epoch: int) -> dict[str, object]:
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    installed = installation.validate(install_result_raw)
    ceremony = decode_unique_json(ceremony_raw)
    runtime = decode_unique_json(runtime_raw)
    measured = checkpoint_owner._measurement(
        measurement_raw, plan_raw=plan_raw, target=target,
        checkpoint_epoch=now_epoch)
    runtime_fields = {"schema", "plan_sha256", "install_result_sha256",
                      "measurement_sha256", "observed_epoch", "target_sha256",
                      "repair_checkpoint_absent", "temporary_absent",
                      "ledger_absent", "operation_process_absent",
                      "host_bindings", "signer_invoked", "private_key_accessed",
                      "production_health", "automatic_routing"}
    if (installed["inactive"] is not True
            or installed["effect_authorized"] is not False
            or sha256(install_result_raw) != INSTALL_RESULT_SHA256
            or not isinstance(ceremony, dict)
            or ceremony.get("plan_sha256") != sha256(plan_raw)
            or ceremony.get("effect_authorized") is not False
            or ceremony.get("grant_consumed") is not False
            or ceremony.get("maximum_effects") != 0
            or ceremony.get("preflight_eligible") is not False
            or ceremony.get("automatic_routing") != "off"
            or not isinstance(runtime, dict) or set(runtime) != runtime_fields
            or runtime["schema"] != "aster-sa4-zero-effect-runtime-state.v1"
            or runtime["plan_sha256"] != sha256(plan_raw)
            or runtime["install_result_sha256"] != INSTALL_RESULT_SHA256
            or runtime["measurement_sha256"] != sha256(measurement_raw)
            or runtime["observed_epoch"] != now_epoch
            or runtime["target_sha256"]
            != plan["precondition"]["expected_sha256"]
            or runtime["target_sha256"]
            != measured["target_snapshot"]["bytes_sha256"]
            or runtime["repair_checkpoint_absent"] is not True
            or runtime["temporary_absent"] is not True
            or runtime["ledger_absent"] is not True
            or runtime["operation_process_absent"] is not True
            or runtime["host_bindings"] != HOST_BINDINGS
            or runtime["signer_invoked"] is not False
            or runtime["private_key_accessed"] is not False
            or runtime["production_health"] != {name: True for name in HEALTH}
            or runtime["automatic_routing"] != "off"):
        raise ValueError("SA4 zero-effect dry preflight changed")
    return {
        "schema": "aster-sa4-zero-effect-dry-preflight.v1",
        "plan_sha256": sha256(plan_raw),
        "install_result_sha256": INSTALL_RESULT_SHA256,
        "measurement_sha256": sha256(measurement_raw),
        "runtime_sha256": sha256(runtime_raw),
        "target_registration_sha256": registry.registration_sha256(target),
        "target_sha256": runtime["target_sha256"],
        "dry_preflight_complete": True, "effect_authorized": False,
        "maximum_effects": 0, "preflight_eligible": False,
        "owner_effect_approval_required": True,
        "automatic_retry": False, "automatic_routing": "off"}
