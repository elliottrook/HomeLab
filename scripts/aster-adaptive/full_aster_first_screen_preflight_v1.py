"""Pure admission check for the full-Aster two-request challenger screen."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, time as wall_time
from zoneinfo import ZoneInfo

SCHEMA = "aster-full-path-first-screen-preflight.v1"
EXPECTED_ARTIFACT = {
    "path": "/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1/Qwen3.6-35B-A3B-Q4_K_M.gguf",
    "bytes": 20419565568,
    "sha256": "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7",
    "owner": "root:root", "mode": "0400", "guest_mount_absent": True}
BASELINE_MODEL = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
RUNTIME = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
ZONE = ZoneInfo("America/Vancouver")
PROTECTED_TIME = wall_time(4, 15)
MIN_RECOVERY_SECONDS = 900


def _validate_contract(raw):
    try:
        value = json.loads(raw)
    except (UnicodeError, json.JSONDecodeError, TypeError) as error:
        raise ValueError("benchmark contract is not valid JSON") from error
    try:
        exact = (
            value["schema"] == "aster-full-path-benchmark-contract.v1"
            and value["status"] == "owner-frozen"
            and value["authority"] == "not-granted"
            and value["case_packet"]["cases"] == 24
            and set(value["case_packet"]["families"].values()) == {4}
            and len(value["case_packet"]["families"]) == 6
            and value["models"]["baseline"] == {
                "identity_sha256": BASELINE_MODEL,
                "mode": "reasoning-off", "runtime_sha256": RUNTIME}
            and value["models"]["challenger"] == {
                "identity_sha256": EXPECTED_ARTIFACT["sha256"],
                "mode": "reasoning-on-27b-plus", "runtime_sha256": RUNTIME}
            and value["resources"]["model_calls_max"] == 48
            and value["resources"]["retries_max"] == 0
            and value["recovery"] == {
                "exact_baseline_restore": True, "f6_required": True,
                "independent_observer_required": True,
                "uncertain_recovery_rejects_result": True})
    except (KeyError, TypeError):
        exact = False
    if not exact:
        raise ValueError("benchmark contract semantics differ")


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= set("0123456789abcdef")


def validate(document, contract_raw, *, now_epoch):
    if type(now_epoch) is not int or now_epoch <= 0:
        raise ValueError("current time is invalid")
    _validate_contract(contract_raw)
    contract_sha = hashlib.sha256(contract_raw).hexdigest()
    required = {"schema", "cycle_date", "contract_sha256", "artifact",
                "evidence", "lease", "watchdog", "baseline", "production",
                "window", "authority"}
    if (not isinstance(document, dict) or set(document) != required
            or document["schema"] != SCHEMA
            or document["contract_sha256"] != contract_sha
            or document["authority"] != "not-granted"
            or document["artifact"] != EXPECTED_ARTIFACT):
        raise ValueError("first-screen preflight boundary differs")
    cycle = document["cycle_date"]
    evidence = document["evidence"]
    try:
        local = datetime.fromtimestamp(now_epoch, ZONE)
        cycle_value = datetime.strptime(cycle, "%Y-%m-%d").date()
    except (TypeError, ValueError, OSError) as error:
        raise ValueError("same-cycle date is invalid") from error
    if (cycle_value != local.date()
            or set(evidence) != {"f2", "f3", "f4", "f5"}
            or any(not _sha(value) for value in evidence.values())):
        raise ValueError("same-cycle evidence differs")
    if document["lease"] != {"state": "ready", "lease_absent": True,
                             "lock_absent": True, "operation_lock_absent": True}:
        raise ValueError("lease is not ready")
    watchdog = document["watchdog"]
    if (set(watchdog) != {"armed", "independent", "owner_alive",
                         "recovery_deadline_epoch", "controller_deadline_epoch"}
            or watchdog["armed"] is not True or watchdog["independent"] is not True
            or watchdog["owner_alive"] is not True
            or type(watchdog["recovery_deadline_epoch"]) is not int
            or type(watchdog["controller_deadline_epoch"]) is not int
            or watchdog["controller_deadline_epoch"] <= now_epoch
            or watchdog["recovery_deadline_epoch"] - watchdog["controller_deadline_epoch"]
               < MIN_RECOVERY_SECONDS):
        raise ValueError("watchdog boundary differs")
    if document["baseline"] != {"model_sha256": BASELINE_MODEL,
                                "runtime_sha256": RUNTIME,
                                "service_healthy": True,
                                "authenticated_response": True}:
        raise ValueError("baseline identity differs")
    production = document["production"]
    if (set(production) != {"lxc104_running", "lxc110_running", "lxc116_running",
                           "aster_agent_healthy", "speech_healthy",
                           "schedules_exact", "competing_work_absent"}
            or not all(value is True for value in production.values())):
        raise ValueError("production baseline differs")
    window = document["window"]
    if (set(window) != {"after_0300_pull", "outage_budget_seconds",
                       "restore_reserve_seconds", "protected_deadline_epoch"}
            or window["after_0300_pull"] is not True
            or type(window["outage_budget_seconds"]) is not int
            or not 0 < window["outage_budget_seconds"] <= 5400
            or type(window["restore_reserve_seconds"]) is not int
            or window["restore_reserve_seconds"] < MIN_RECOVERY_SECONDS
            or type(window["protected_deadline_epoch"]) is not int
            or watchdog["recovery_deadline_epoch"] > window["protected_deadline_epoch"]
            or watchdog["recovery_deadline_epoch"] - watchdog["controller_deadline_epoch"]
               < window["restore_reserve_seconds"]
            or datetime.fromtimestamp(window["protected_deadline_epoch"], ZONE)
               != datetime.combine(cycle_value, PROTECTED_TIME, tzinfo=ZONE)
            or local.time() < wall_time(3, 0)
            or watchdog["controller_deadline_epoch"] - now_epoch
               > window["outage_budget_seconds"]):
        raise ValueError("screen window differs")
    return {"schema": "aster-full-path-first-screen-admission.v1",
            "cycle_date": cycle, "contract_sha256": contract_sha,
            "evidence": evidence, "admitted": True,
            "live_effect_authorized": False, "authority": "not-granted"}
