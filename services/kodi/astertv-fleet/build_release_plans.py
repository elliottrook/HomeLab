#!/usr/bin/env python3
"""Generate deterministic, non-deploying AsterTV release plans and SBOMs."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import importlib.util
import io
import json
import os
import tarfile
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def deterministic_bundle(checkout: Path, artifact_path: Path, release: dict,
                         desired: dict, guard: dict) -> bytes:
    """Build a byte-stable appliance bundle from verified source bytes."""
    manifest = {
        "schema_version": 1,
        "kind": "astertv-composition-bundle",
        "device_id": desired["device_id"],
        "composition_sha256": desired["composition_sha256"],
        "release": {
            "id": release["id"],
            "path": f'release/{release["artifact"]["name"]}',
            "sha256": release["artifact"]["sha256"],
        },
        "overlays": [{
            "id": overlay_id,
            "payloads": desired["payloads"][overlay_id],
        } for overlay_id in desired["overlays"]],
        "guard": guard,
    }
    members: list[tuple[str, bytes, int]] = [
        ("manifest.json", canonical(manifest), 0o644),
        ("guard-contract.json", canonical(guard), 0o644),
        (f'release/{release["artifact"]["name"]}', artifact_path.read_bytes(), 0o644),
    ]
    for overlay_id in desired["overlays"]:
        for payload in desired["payloads"][overlay_id]:
            source = checkout / payload["path"]
            data = source.read_bytes()
            if len(data) != payload["bytes"] or hashlib.sha256(data).hexdigest() != payload["sha256"]:
                raise FLEET.FleetError(f'payload-drift:{overlay_id}:{payload["path"]}')
            mode = 0o755 if os.access(source, os.X_OK) else 0o644
            members.append((f'overlays/{overlay_id}/{payload["path"]}', data, mode))
    stream = io.BytesIO()
    with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as archive:
            for name, data, mode in sorted(members):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = mode
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = "root"
                archive.addfile(info, io.BytesIO(data))
    return stream.getvalue()


def installed_payloads(checkout: Path, desired: dict, overlays: dict[str, dict]) -> dict[str, list[dict]]:
    """Resolve materialized destination bytes for live guard observation."""
    result: dict[str, list[dict]] = {}
    for overlay_id in desired["overlays"]:
        overlay = overlays[overlay_id]
        rows = []
        manifests = [item for item in desired["payloads"][overlay_id]
                     if item["path"].endswith("materialization-manifest.json")]
        for manifest_row in manifests:
            manifest = load(checkout / manifest_row["path"])
            if (manifest.get("kind") != "astertv-materialized-overlay" or
                    manifest.get("id") != overlay_id):
                raise FLEET.FleetError(f"materialization-identity:{overlay_id}")
            candidates = list(manifest.get("files", [])) + list(manifest.get("outputs", []))
            for item in candidates:
                scope = item.get("scope", "common")
                if scope not in {"common", desired["device_id"]}:
                    continue
                required = ("destination", "sha256", "bytes", "mode")
                if not all(key in item for key in required):
                    raise FLEET.FleetError(f"materialization-row:{overlay_id}")
                rows.append({key: item[key] for key in required})
        if overlay.get("payload_status") == "complete" and not rows and overlay.get("apply_strategy", "install") != "preserve-and-verify":
            raise FLEET.FleetError(f"complete-payload-without-materialization:{overlay_id}")
        result[overlay_id] = sorted(rows, key=lambda row: row["destination"])
    return result


def build(root: Path, output: Path, artifact_root: Path | None = None) -> dict:
    root = root.resolve()
    output = output.resolve()
    with tempfile.TemporaryDirectory(prefix="astertv-plan-compositions-") as compiled:
        compositions = FLEET.compile_fleet(root, Path(compiled))
    releases = {item["id"]: item for item in (FLEET.load_json_yaml(path) for path in sorted((root / "releases").glob("*.yaml")))}
    overlays = {item["id"]: item for item in (FLEET.load_json_yaml(path) for path in sorted((root / "overlays").glob("*.yaml")))}
    budgets = load(root / "policies/performance-budgets.json")
    compatibility = load(root / "policies/compatibility.json")
    artifact_root = artifact_root.resolve() if artifact_root else None
    checkout = FLEET.repository_root(root)
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
        installed = installed_payloads(checkout, desired, overlays)
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
                "payloads": desired["payloads"][overlay_id],
                "payload_status": overlay.get("payload_status", "incomplete"),
                "payload_blockers": overlay.get("payload_blockers", ["payload-contract-not-reviewed"]),
                "apply_strategy": overlay.get("apply_strategy", "install"),
                "assertions": overlay.get("assertions", []),
                "installed_payloads": installed[overlay_id],
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
        artifact_path = artifact_root / release["artifact"]["name"] if artifact_root else None
        artifact_verified = False
        artifact_observed_sha256 = None
        if artifact_path and artifact_path.is_file():
            artifact_observed_sha256 = file_sha256(artifact_path)
            if artifact_observed_sha256 != release["artifact"]["sha256"]:
                raise FLEET.FleetError(f'artifact-hash-mismatch:{release["id"]}')
            artifact_verified = True
        guard = {
            "schema_version": 1,
            "kind": "composition-guard-contract",
            "device_id": desired["device_id"],
            "hostname": desired["hostname"],
            "composition_sha256": desired["composition_sha256"],
            "expected_resources": sorted(desired["ownership"]),
            "expected_payloads": [
                {"overlay": overlay_id, "path": payload["destination"],
                 "sha256": payload["sha256"], "bytes": payload["bytes"],
                 "mode": payload["mode"]}
                for overlay_id in desired["overlays"]
                for payload in installed[overlay_id]
            ],
            "registered_extras": [],
            "mutable_exclusions": ["userdata/Database", "userdata/Thumbnails", "userdata/addon_data", "cache", "temp"],
            "required_dependencies": sorted(desired["external_integrations"]),
            "expected_assertions": [
                dict(assertion, overlay=overlay_id)
                for overlay_id in desired["overlays"]
                for assertion in overlays[overlay_id].get("assertions", [])
            ],
            "dependency_policy": "all-required-available",
        }
        bundle_name = f'{desired["device_id"]}-{desired["composition_sha256"][:12]}.tar.gz'
        bundle_sha256 = None
        bundle_bytes = None
        if artifact_verified:
            bundle = deterministic_bundle(checkout, artifact_path, release, desired, guard)
            bundle_sha256 = hashlib.sha256(bundle).hexdigest()
            bundle_bytes = len(bundle)
            atomic_write(output / "bundles" / bundle_name, bundle)
        blockers = []
        if not artifact_verified:
            blockers.append("release-artifact-not-locally-verified")
        if bundle_sha256 is None:
            blockers.append("composition-bundle-not-built")
        for overlay_id in desired["overlays"]:
            if overlays[overlay_id].get("payload_status") != "complete":
                blockers.append(f"overlay-payload-incomplete:{overlay_id}")
        if not desired["deployed"]:
            blockers.append("candidate-not-deployable")
        deployable = not blockers
        plan = {
            "schema_version": 1,
            "kind": "release-plan",
            "device_id": desired["device_id"],
            "composition_sha256": desired["composition_sha256"],
            "release": desired["release"],
            "artifact": {
                "name": release["artifact"]["name"],
                "expected_sha256": release["artifact"]["sha256"],
                "observed_sha256": artifact_observed_sha256,
                "verified": artifact_verified,
            },
            "bundle": {
                "name": bundle_name,
                "sha256": bundle_sha256,
                "bytes": bundle_bytes,
                "built": bundle_sha256 is not None,
            },
            "compatibility": release["compatibility"],
            "performance_budget": budget,
            "overlays": overlay_rows,
            "owned_resources": sorted(desired["ownership"]),
            "promotion_policy": compatibility,
            "promotion_blockers": blockers,
            "deployable": deployable,
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
        atomic_write(output / "plans" / f'{desired["device_id"]}.json', canonical(plan))
        atomic_write(output / "sbom" / f'{desired["device_id"]}.cdx.json', canonical(sbom))
        atomic_write(output / "guards" / f'{desired["device_id"]}.json', canonical(guard))
        results.append({"device_id": desired["device_id"], "blockers": blockers, "components": len(components), "artifact_verified": artifact_verified, "bundle_built": bundle_sha256 is not None, "bundle_sha256": bundle_sha256})
    deployable_devices = sum(1 for row in results if not row["blockers"])
    summary = {"schema_version": 1, "kind": "release-plan-summary", "devices": results, "deployable_devices": deployable_devices, "verified_artifacts": sum(1 for row in results if row["artifact_verified"]), "built_bundles": sum(1 for row in results if row["bundle_built"]), "mode": "bundle-build" if artifact_root else "plan-only"}
    atomic_write(output / "release-plan-summary.json", canonical(summary))
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=HERE)
    parser.add_argument("--output", type=Path, default=HERE / "generated-release-plans")
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build(args.root, args.output, args.artifact_root)
    except FLEET.FleetError as exc:
        parser.exit(2, f"release planning failed: {exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
