#!/usr/bin/env python3
"""Generate deterministic, non-deploying AsterTV release plans and SBOMs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("astertv_compile_fleet", HERE / "compile_fleet.py")
FLEET = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(FLEET)


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def build(root: Path, output: Path) -> dict:
    root = root.resolve()
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="astertv-plan-compositions-") as compiled:
        compositions = FLEET.compile_fleet(root, Path(compiled))
    releases = {item["id"]: item for item in (FLEET.load_json_yaml(path) for path in sorted((root / "releases").glob("*.yaml")))}
    overlays = {item["id"]: item for item in (FLEET.load_json_yaml(path) for path in sorted((root / "overlays").glob("*.yaml")))}
    budgets = load(root / "policies/performance-budgets.json")
    compatibility = load(root / "policies/compatibility.json")
    results = []
    for desired in compositions:
        release = releases[desired["release"]]
        budget = budgets["profiles"].get(desired["hardware_profile"])
        if budget is None:
            raise FLEET.FleetError(f'missing-performance-budget:{desired["hardware_profile"]}')
        components = [{
            "type": "application",
            "name": release["artifact"]["name"],
            "version": release["id"],
            "hashes": [{"alg": "SHA-256", "content": release["artifact"]["sha256"]}],
            "properties": [{"name": "astertv:authority", "value": release["artifact"]["authority"]}],
        }]
        overlay_rows = []
        for overlay_id in desired["overlays"]:
            overlay = overlays[overlay_id]
            overlay_rows.append({
                "id": overlay_id,
                "owner": overlay["owner"],
                "layer": overlay["layer"],
                "dependencies": overlay["dependencies"],
                "owns": overlay["owns"],
                "tests": overlay["tests"],
                "rollback_ref": overlay["rollback_ref"],
            })
            components.append({
                "type": "application",
                "name": overlay_id,
                "version": "composition-" + desired["composition_sha256"][:12],
                "properties": [
                    {"name": "astertv:owner", "value": overlay["owner"]},
                    {"name": "astertv:layer", "value": overlay["layer"]},
                ],
            })
        blockers = ["release-artifact-not-locally-verified"]
        if not desired["deployed"]:
            blockers.append("candidate-not-deployable")
        plan = {
            "schema_version": 1,
            "kind": "release-plan",
            "device_id": desired["device_id"],
            "composition_sha256": desired["composition_sha256"],
            "release": desired["release"],
            "compatibility": release["compatibility"],
            "performance_budget": budget,
            "overlays": overlay_rows,
            "owned_resources": sorted(desired["ownership"]),
            "promotion_policy": compatibility,
            "promotion_blockers": blockers,
            "deployable": False,
            "required_runtime_gates": ["identity", "idle", "checkpoint", "artifact-hash", "composition", "tests", "rollback"],
        }
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "serialNumber": "urn:uuid:astertv-" + desired["composition_sha256"][:32],
            "metadata": {"component": {"type": "device", "name": desired["device_id"], "version": desired["composition_sha256"][:12]}},
            "components": components,
        }
        guard = {
            "schema_version": 1,
            "kind": "composition-guard-contract",
            "device_id": desired["device_id"],
            "composition_sha256": desired["composition_sha256"],
            "expected_resources": sorted(desired["ownership"]),
            "registered_extras": [],
            "mutable_exclusions": ["userdata/Database", "userdata/Thumbnails", "userdata/addon_data", "cache", "temp"],
            "dependency_policy": "all-required-available",
        }
        atomic_write(output / "plans" / f'{desired["device_id"]}.json', canonical(plan))
        atomic_write(output / "sbom" / f'{desired["device_id"]}.cdx.json', canonical(sbom))
        atomic_write(output / "guards" / f'{desired["device_id"]}.json', canonical(guard))
        results.append({"device_id": desired["device_id"], "blockers": blockers, "components": len(components)})
    summary = {"schema_version": 1, "kind": "release-plan-summary", "devices": results, "deployable_devices": 0, "mode": "plan-only"}
    atomic_write(output / "release-plan-summary.json", canonical(summary))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--output", type=Path, default=HERE / "generated-release-plans")
    args = parser.parse_args(argv)
    try:
        result = build(args.root, args.output)
    except FLEET.FleetError as exc:
        parser.exit(2, f"release planning failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
