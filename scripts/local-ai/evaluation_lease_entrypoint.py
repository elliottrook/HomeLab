"""Explicit-phase platform entry point for the Stream A evaluation lease.

There is no automatic activation path.  Without ``--effect-authorized`` this
program does not read state or intent and reports a disabled result.  A future
manual invocation must provide one strict phase payload and run as root.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from evaluation_lease import Admission, ProductionBaseline, WorkloadOutcome
from evaluation_lease_adapter import EvaluationLeaseAdapter


class EntryPointError(ValueError):
    pass


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
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            fd = -1
            value = json.load(stream, object_pairs_hook=_unique_pairs)
    finally:
        if fd != -1:
            os.close(fd)
    if not isinstance(value, dict):
        raise EntryPointError("intent must be a JSON object")
    return value


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
    if set(value) != required:
        raise EntryPointError("acquire intent keys are not exact")
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
    if os.geteuid() != 0:
        raise EntryPointError("effectful evaluation entry point requires root")
    adapter = EvaluationLeaseAdapter(args.state, _runner, allow_effects=True)
    phase = args.phase
    if phase == "acquire":
        admission = _admission(intent)
        return adapter.acquire(admission, now_epoch=intent["now_epoch"])
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
            recovery=bool(intent.get("recovery", False)),
        )
    raise EntryPointError("unsupported phase")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("acquire", "post-quiescence", "heartbeat", "start", "outcome", "restore"), required=True)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--intent", type=Path, required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
        return 0
    try:
        result = _main_effectful(args, load_intent(args.intent))
    except Exception as exc:
        print(json.dumps({"effects": "failed-closed", "error": type(exc).__name__}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
