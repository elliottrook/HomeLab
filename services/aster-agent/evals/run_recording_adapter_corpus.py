#!/usr/bin/env python3
"""Run a sealed synthetic corpus through Aster's zero-effect recording adapter."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from local_orchestrator import (  # noqa: E402
    ProviderRegistrySnapshot,
    RegistryRecordingAdapter,
    execute_household,
    plan_household,
)


def run(suite: dict) -> dict:
    if suite.get("schema_version") != 1 or suite.get("status") != "sealed":
        raise ValueError("only a sealed schema-version 1 corpus may run")
    raw_snapshot = suite["snapshot"]
    snapshot = ProviderRegistrySnapshot(
        raw_snapshot["schema_version"], raw_snapshot["snapshot_id"],
        tuple(raw_snapshot.get("timers", [])), tuple(raw_snapshot.get("rooms", [])),
        tuple(raw_snapshot.get("entities", [])), tuple(raw_snapshot.get("media_providers", [])),
    )
    state = snapshot.household_state()
    results = []
    for case in suite["cases"]:
        adapter = RegistryRecordingAdapter(snapshot, max_calls=1)
        decision = plan_household(case["text"], state)
        failures = []
        if decision.status != case["status"]:
            failures.append(f"status: expected {case['status']!r}, got {decision.status!r}")
        if decision.status == "plan":
            result = execute_household(decision, adapter)
            if decision.capability != case.get("capability"):
                failures.append(f"capability: expected {case.get('capability')!r}, got {decision.capability!r}")
            if decision.arguments != case.get("arguments"):
                failures.append(f"arguments: expected {case.get('arguments')!r}, got {decision.arguments!r}")
            if result.get("effect_permitted") is not False:
                failures.append("recording adapter permitted an effect")
        elif adapter.calls:
            failures.append("non-plan reached the recording adapter")
        results.append({"id": case["id"], "passed": not failures, "failures": failures,
                        "status": decision.status, "recorded_calls": adapter.calls})
    encoded_suite = (json.dumps(suite, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return {
        "schema_version": 1,
        "suite_id": suite["suite_id"],
        "suite_sha256": hashlib.sha256(encoded_suite).hexdigest(),
        "pass_count": sum(item["passed"] for item in results),
        "case_count": len(results),
        "effect_count": sum(call["effect_permitted"] is not False for item in results for call in item["recorded_calls"]),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    suite = json.loads(args.cases.read_text())
    report = run(suite)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        with args.output.open("x") as handle:
            handle.write(rendered)
    print(json.dumps({key: report[key] for key in ("suite_sha256", "pass_count", "case_count", "effect_count")}, sort_keys=True))
    return 0 if report["pass_count"] == report["case_count"] and report["effect_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
