"""Pure admission check for the full-Aster two-request challenger screen."""
from __future__ import annotations

import hashlib
import json

SCHEMA = "aster-full-path-first-screen-preflight.v1"
EXPECTED_ARTIFACT = {
    "path": "/var/lib/vz/aster-model-staging/qwen36-35b-a3b-v1/Qwen3.6-35B-A3B-Q4_K_M.gguf",
    "bytes": 20419565568,
    "sha256": "671e47e0ec53c665d048b98c3ecbfd5236b5ca9c3e02ed19fc8f81f7b85140c7",
    "owner": "root:root", "mode": "0400", "guest_mount_absent": True}
BASELINE_MODEL = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
RUNTIME = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= set("0123456789abcdef")


def validate(document, contract_raw):
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
    if (not isinstance(cycle, str) or len(cycle) != 10
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
            or watchdog["recovery_deadline_epoch"] <= watchdog["controller_deadline_epoch"]):
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
            or window["restore_reserve_seconds"] < 900
            or type(window["protected_deadline_epoch"]) is not int
            or watchdog["recovery_deadline_epoch"] > window["protected_deadline_epoch"]):
        raise ValueError("screen window differs")
    return {"schema": "aster-full-path-first-screen-admission.v1",
            "cycle_date": cycle, "contract_sha256": contract_sha,
            "evidence": evidence, "admitted": True,
            "live_effect_authorized": False, "authority": "not-granted"}
