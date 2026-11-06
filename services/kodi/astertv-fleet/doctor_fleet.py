#!/usr/bin/env python3
"""Fail-closed Doctor report over sanitized AsterTV observations."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astertv_composition_guard", HERE / "composition_guard.py")
GUARD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GUARD)


def parse_time(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("observation-time")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("observation-timezone")
    return parsed.astimezone(timezone.utc)


def report(root: Path, observed: Path, now: datetime, max_age: timedelta) -> dict:
    devices = []
    for device_path in sorted((root / "devices").glob("*.yaml")):
        device = json.loads(device_path.read_text())
        if not device.get("deployed"):
            continue
        device_id = device["id"]
        contract_path = root / "generated-release-plans/guards" / f"{device_id}.json"
        observation_path = observed / f"{device_id}.json"
        row = {"device_id": device_id, "hostname": device["hostname"]}
        if not contract_path.is_file():
            row.update(status="invalid", reason="guard-contract-missing")
        elif not observation_path.is_file():
            row.update(status="unobserved", reason="observation-missing")
        else:
            try:
                observation = json.loads(observation_path.read_text())
                observed_at = parse_time(observation.get("observed_at"))
                if observed_at > now + timedelta(minutes=5):
                    raise ValueError("observation-from-future")
                age = now - observed_at
                if age > max_age:
                    row.update(status="stale", reason="observation-expired",
                               age_seconds=int(age.total_seconds()))
                else:
                    result = GUARD.inspect(json.loads(contract_path.read_text()), observation)
                    row.update(status=result["outcome"], reason=None,
                               age_seconds=int(age.total_seconds()), result=result)
            except (OSError, ValueError, json.JSONDecodeError) as error:
                row.update(status="invalid", reason=str(error))
        devices.append(row)
    counts = {status: sum(row["status"] == status for row in devices)
              for status in ("clean", "registered-extra", "drift", "stale", "unobserved", "invalid")}
    outcome = "clean" if counts["clean"] + counts["registered-extra"] == len(devices) else "attention"
    return {"schema_version": 1, "kind": "astertv-doctor-report",
            "outcome": outcome, "counts": counts, "devices": devices}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--observed", type=Path, default=HERE / "observed")
    parser.add_argument("--now")
    parser.add_argument("--max-age-hours", type=int, default=24)
    args = parser.parse_args(argv)
    now = parse_time(args.now) if args.now else datetime.now(timezone.utc)
    result = report(args.root.resolve(), args.observed.resolve(), now,
                    timedelta(hours=args.max_age_hours))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] == "clean" else 1


if __name__ == "__main__":
    raise SystemExit(main())
