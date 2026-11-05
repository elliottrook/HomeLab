#!/usr/bin/env python3
"""Classify sanitized AsterTV observations against a compiled guard contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def inspect(contract: dict, observed: dict) -> dict:
    if contract.get("schema_version") != 1 or contract.get("kind") != "composition-guard-contract":
        raise ValueError("guard-contract-schema")
    if observed.get("schema_version") != 1 or observed.get("kind") != "composition-observation":
        raise ValueError("observation-schema")
    if observed.get("device_id") != contract["device_id"]:
        raise ValueError("device-identity-mismatch")
    expected = set(contract["expected_resources"])
    registered = set(contract.get("registered_extras", []))
    resources = observed.get("resources")
    if not isinstance(resources, list) or any(not isinstance(item, str) for item in resources):
        raise ValueError("observation-resources")
    actual = set(resources)
    missing = sorted(expected - actual)
    registered_extra = sorted((actual - expected) & registered)
    unknown = sorted(actual - expected - registered)
    unavailable = sorted(name for name, state in observed.get("dependencies", {}).items() if state != "available")
    composition_mismatch = observed.get("composition_sha256") != contract["composition_sha256"]
    outcome = "clean"
    if missing or unknown or unavailable or composition_mismatch:
        outcome = "drift"
    elif registered_extra:
        outcome = "registered-extra"
    return {
        "schema_version": 1,
        "device_id": contract["device_id"],
        "outcome": outcome,
        "composition_mismatch": composition_mismatch,
        "missing": missing,
        "registered_extras": registered_extra,
        "unknown": unknown,
        "unavailable_dependencies": unavailable,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("contract", type=Path)
    parser.add_argument("observation", type=Path)
    args = parser.parse_args(argv)
    result = inspect(json.loads(args.contract.read_text()), json.loads(args.observation.read_text()))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["outcome"] in {"clean", "registered-extra"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
