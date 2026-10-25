"""Explicit-phase platform entry point for the Stream A evaluation lease.

There is no automatic activation path.  Without ``--effect-authorized`` this
program does not read state or intent and reports a disabled result.  A future
manual invocation must provide one strict phase payload and run as root.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

from evaluation_lease import Admission, ProductionBaseline, WorkloadOutcome
from evaluation_lease_adapter import EvaluationLeaseAdapter


class EntryPointError(ValueError):
    pass


DEFAULT_STATE_PATH = Path("/var/lib/local-ai-lab/stream-a-evaluation/lease.json")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EntryPointError("intent contains duplicate JSON keys")
        result[key] = value
    return result


def load_intent(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise EntryPointError("intent cannot be opened safely") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or (info.st_mode & 0o777) != 0o600):
            raise EntryPointError("intent custody must be root-owned mode 0600")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            value = json.load(stream, object_pairs_hook=_unique_pairs)
    finally:
        if fd != -1:
            os.close(fd)
    if not isinstance(value, dict):
        raise EntryPointError("intent must be a JSON object")
    return value


def _exact(value: dict[str, Any], keys: set[str], phase: str) -> None:
    if set(value) != keys:
        raise EntryPointError(f"{phase} intent keys are not exact")


def _str(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        raise EntryPointError(f"{name} must be a non-empty string")


def _int(value: object, name: str) -> None:
    if type(value) is not int:
        raise EntryPointError(f"{name} must be an integer")


def _bool(value: object, name: str) -> None:
    if type(value) is not bool:
        raise EntryPointError(f"{name} must be a literal boolean")


def validate_phase_intent(phase: str, value: dict[str, Any]) -> None:
    if phase == "acquire":
        _admission(value)
        return
    if phase == "heartbeat":
        _exact(value, {"lease_id", "generation", "now_epoch"}, phase)
        _str(value["lease_id"], "lease_id"); _int(value["generation"], "generation")
        _int(value["now_epoch"], "now_epoch")
        return
    if phase == "quiesce":
        _exact(value, {"lease_id", "generation", "now_epoch", "heartbeat_timeout"}, phase)
        _str(value["lease_id"], "lease_id"); _int(value["generation"], "generation")
        _int(value["now_epoch"], "now_epoch"); _int(value["heartbeat_timeout"], "heartbeat_timeout")
        return
    if phase == "start":
        _exact(value, {"lease_id", "generation", "workload_name", "now_epoch", "heartbeat_timeout"}, phase)
        _str(value["lease_id"], "lease_id"); _int(value["generation"], "generation")
        _str(value["workload_name"], "workload_name"); _int(value["now_epoch"], "now_epoch")
        _int(value["heartbeat_timeout"], "heartbeat_timeout")
        return
    if phase == "outcome":
        _exact(value, {"lease_id", "generation", "name", "packet_digest", "status",
                       "journal_digest", "result_digest", "calls", "elapsed_seconds",
                       "tool_free", "transport_uncertain", "now_epoch", "heartbeat_timeout"}, phase)
        for name in ("lease_id", "name", "packet_digest", "status", "journal_digest", "result_digest"):
            _str(value[name], name)
        for name in ("generation", "calls", "elapsed_seconds", "now_epoch", "heartbeat_timeout"):
            _int(value[name], name)
        _bool(value["tool_free"], "tool_free"); _bool(value["transport_uncertain"], "transport_uncertain")
        return
    if phase == "restore":
        _exact(value, {"lease_id", "generation", "restored_baseline", "backend_active",
                       "endpoint_authenticated", "endpoint_idle", "gpu_holders", "recovery"}, phase)
        _str(value["lease_id"], "lease_id"); _int(value["generation"], "generation")
        _bool(value["backend_active"], "backend_active")
        _bool(value["endpoint_authenticated"], "endpoint_authenticated")
        _bool(value["endpoint_idle"], "endpoint_idle"); _bool(value["recovery"], "recovery")
        if not isinstance(value["gpu_holders"], list) or any(not isinstance(item, str) for item in value["gpu_holders"]):
            raise EntryPointError("gpu_holders must be a string list")
        _baseline(value["restored_baseline"])
        return
    if phase == "post-quiescence":
        _exact(value, {"admission", "observed_states", "backend_active", "endpoint_authenticated",
                       "endpoint_idle", "gpu_holders", "now_epoch", "heartbeat_timeout"}, phase)
        if not isinstance(value["admission"], dict):
            raise EntryPointError("admission must be an object")
        _admission(value["admission"])
        if not isinstance(value["observed_states"], list):
            raise EntryPointError("observed_states must be a list")
        _bool(value["backend_active"], "backend_active"); _bool(value["endpoint_authenticated"], "endpoint_authenticated")
        _bool(value["endpoint_idle"], "endpoint_idle"); _int(value["now_epoch"], "now_epoch")
        _int(value["heartbeat_timeout"], "heartbeat_timeout")
        if not isinstance(value["gpu_holders"], list) or any(not isinstance(item, str) for item in value["gpu_holders"]):
            raise EntryPointError("gpu_holders must be a string list")
        return
    raise EntryPointError("unsupported phase")


def _baseline(value: object) -> ProductionBaseline:
    if not isinstance(value, dict) or set(value) != {"units", "timers"}:
        raise EntryPointError("baseline schema is invalid")
    try:
        units = tuple((str(item[0]), str(item[1])) for item in value["units"])
        timers = tuple((str(item[0]), str(item[1])) for item in value["timers"])
    except (TypeError, IndexError, KeyError) as exc:
        raise EntryPointError("baseline records are invalid") from exc
    return ProductionBaseline(units, timers)


def _admission(value: dict[str, Any]) -> Admission:
    required = {
        "lease_id", "generation", "backup_receipt", "f2_receipt", "f3_receipt",
        "model", "backend", "endpoint", "backend_active",
        "endpoint_authenticated", "endpoint_idle", "gpu_holders",
        "registered_targets", "quiesced_targets", "baseline",
        "watchdog_independent", "hard_deadline_epoch", "restore_deadline_epoch",
        "now_epoch",
    }
    _exact(value, required, "acquire")
    for name in ("lease_id", "backup_receipt", "f2_receipt", "f3_receipt", "model", "backend", "endpoint"):
        _str(value[name], name)
    _int(value["generation"], "generation"); _int(value["hard_deadline_epoch"], "hard_deadline_epoch")
    _int(value["restore_deadline_epoch"], "restore_deadline_epoch"); _int(value["now_epoch"], "now_epoch")
    for name in ("backend_active", "endpoint_authenticated", "endpoint_idle", "watchdog_independent"):
        _bool(value[name], name)
    for name in ("gpu_holders", "registered_targets", "quiesced_targets"):
        if not isinstance(value[name], list) or any(not isinstance(item, str) for item in value[name]):
            raise EntryPointError(f"{name} must be a string list")
    return Admission(
        value["lease_id"], value["generation"], value["backup_receipt"],
        value["f2_receipt"], value["f3_receipt"], value["model"],
        value["backend"], value["endpoint"], value["backend_active"],
        value["endpoint_authenticated"], value["endpoint_idle"],
        tuple(value["gpu_holders"]), tuple(value["registered_targets"]),
        tuple(value["quiesced_targets"]), _baseline(value["baseline"]),
        value["watchdog_independent"], value["hard_deadline_epoch"],
        value["restore_deadline_epoch"],
    )


def _runner(command):
    subprocess.run(tuple(command), check=True, capture_output=True, text=True, timeout=60)


def _main_effectful(args: argparse.Namespace, intent: dict[str, Any]) -> dict[str, object]:
    if args.state != DEFAULT_STATE_PATH:
        raise EntryPointError("state path is not the fixed watchdog-bound path")
    if os.geteuid() != 0:
        raise EntryPointError("effectful evaluation entry point requires root")
    validate_phase_intent(args.phase, intent)
    adapter = EvaluationLeaseAdapter(args.state, _runner, allow_effects=True)
    phase = args.phase
    if phase == "acquire":
        admission = _admission(intent)
        return adapter.prepare(admission, now_epoch=intent["now_epoch"])
    if phase == "quiesce":
        return adapter.quiesce(lease_id=intent["lease_id"], generation=intent["generation"],
                               now_epoch=intent["now_epoch"],
                               heartbeat_timeout=intent["heartbeat_timeout"])
    if phase == "heartbeat":
        adapter.heartbeat(lease_id=intent["lease_id"], generation=intent["generation"],
                          now_epoch=intent["now_epoch"])
        return {"effects": "heartbeat-recorded"}
    if phase == "post-quiescence":
        admission = _admission(intent["admission"])
        adapter.post_quiescence(
            observed_states=tuple(tuple(item) for item in intent["observed_states"]),
            admission=admission, backend_active=intent["backend_active"],
            endpoint_authenticated=intent["endpoint_authenticated"],
            endpoint_idle=intent["endpoint_idle"],
            gpu_holders=tuple(intent["gpu_holders"]), now_epoch=intent["now_epoch"],
            heartbeat_timeout=intent["heartbeat_timeout"],
        )
        return {"effects": "post-quiescence-recorded"}
    if phase == "start":
        adapter.start_workload(
            lease_id=intent["lease_id"], generation=intent["generation"],
            workload_name=intent["workload_name"], now_epoch=intent["now_epoch"],
            heartbeat_timeout=intent["heartbeat_timeout"],
        )
        return {"effects": "workload-start-recorded"}
    if phase == "outcome":
        outcome = WorkloadOutcome(
            intent["lease_id"], intent["generation"], intent["name"],
            intent["packet_digest"], intent["status"], intent["journal_digest"],
            intent["result_digest"], intent["calls"], intent["elapsed_seconds"],
            intent["tool_free"], intent.get("transport_uncertain", False),
        )
        adapter.record_outcome(outcome, now_epoch=intent["now_epoch"],
                               heartbeat_timeout=intent["heartbeat_timeout"])
        return {"effects": "outcome-recorded"}
    if phase == "restore":
        return adapter.restore(
            lease_id=intent["lease_id"], generation=intent["generation"],
            restored=_baseline(intent["restored_baseline"]),
            backend_active=intent["backend_active"],
            endpoint_authenticated=intent["endpoint_authenticated"],
            endpoint_idle=intent["endpoint_idle"],
            gpu_holders=tuple(intent["gpu_holders"]),
            recovery=intent["recovery"],
        )
    raise EntryPointError("unsupported phase")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("acquire", "quiesce", "post-quiescence", "heartbeat", "start", "outcome", "restore"), required=True)
    parser.add_argument("--state", type=Path, default=DEFAULT_STATE_PATH)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    try:
        if args.state != DEFAULT_STATE_PATH:
            raise EntryPointError("state path is not the fixed watchdog-bound path")
        result = _main_effectful(args, load_intent(args.intent))
    except Exception as exc:
        print(json.dumps({"effects": "failed-closed", "error": type(exc).__name__}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
