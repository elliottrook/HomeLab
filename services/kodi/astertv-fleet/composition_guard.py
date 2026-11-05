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
    required_field = contract.get("required_dependencies")
    required_dependencies = set(required_field or [])
    dependency_states = observed.get("dependencies", {})
    if not isinstance(dependency_states, dict):
        raise ValueError("observation-dependencies")
    unavailable = sorted(
        name for name, state in dependency_states.items() if state != "available"
    ) if required_field is None else sorted(
        name for name in required_dependencies if dependency_states.get(name) != "available"
    )
    expected_payloads = {
        (item["overlay"], item["path"]): item["sha256"]
        for item in contract.get("expected_payloads", [])
    }
    observed_rows = observed.get("payloads", [])
    if not isinstance(observed_rows, list):
        raise ValueError("observation-payloads")
    observed_payloads = {}
    for item in observed_rows:
        if not isinstance(item, dict) or not all(
                isinstance(item.get(key), str) for key in ("overlay", "path", "sha256")):
            raise ValueError("observation-payloads")
        observed_payloads[(item["overlay"], item["path"])] = item["sha256"]
    missing_payloads = sorted(
        f"{overlay}:{path}" for overlay, path in expected_payloads
        if (overlay, path) not in observed_payloads
    )
    payload_mismatches = sorted(
        f"{overlay}:{path}" for (overlay, path), digest in expected_payloads.items()
        if observed_payloads.get((overlay, path), digest) != digest
    )
    unknown_payloads = sorted(
        f"{overlay}:{path}" for overlay, path in observed_payloads
        if (overlay, path) not in expected_payloads
    )
    composition_mismatch = observed.get("composition_sha256") != contract["composition_sha256"]
    outcome = "clean"
    if (missing or unknown or unavailable or composition_mismatch or
            missing_payloads or payload_mismatches or unknown_payloads):
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
        "missing_payloads": missing_payloads,
        "payload_mismatches": payload_mismatches,
        "unknown_payloads": unknown_payloads,
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
