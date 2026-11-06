#!/usr/bin/env python3
"""Compile deterministic AsterTV device compositions without live effects."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path


SCHEMA_VERSION = 1
ACTIVE_STATES = {"lab", "accepted", "production", "degraded"}
LIFECYCLE_STATES = ACTIVE_STATES | {"candidate", "retiring", "retired"}
REF_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
FORBIDDEN_KEYS = {
    "password", "password_hash", "token", "access_token", "refresh_token",
    "api_key", "private_key", "secret", "secret_value", "credential_value",
}


class FleetError(ValueError):
    """A fail-closed fleet contract violation."""


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json_yaml(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise FleetError(f"invalid-manifest:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise FleetError(f"manifest-not-object:{path}")
    _reject_secrets(value, path.as_posix())
    return value


def _reject_secrets(value: object, location: str) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN_KEYS:
                raise FleetError(f"secret-bearing-key:{location}:{key}")
            _reject_secrets(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_secrets(child, f"{location}[{index}]")


def require(document: dict, kind: str, fields: tuple[str, ...], source: Path) -> None:
    if document.get("schema_version") != SCHEMA_VERSION:
        raise FleetError(f"schema-version:{source}")
    if document.get("kind") != kind:
        raise FleetError(f"kind:{source}:{document.get('kind')}")
    missing = [field for field in fields if field not in document]
    if missing:
        raise FleetError(f"missing-fields:{source}:{','.join(missing)}")


def load_directory(root: Path, relative: str, kind: str,
                   fields: tuple[str, ...]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for source in sorted((root / relative).glob("*.yaml")):
        document = load_json_yaml(source)
        require(document, kind, fields, source)
        identifier = document.get("id")
        if not isinstance(identifier, str) or not REF_RE.fullmatch(identifier):
            raise FleetError(f"invalid-id:{source}")
        if identifier in result:
            raise FleetError(f"duplicate-id:{kind}:{identifier}")
        document["_source"] = source.relative_to(root).as_posix()
        result[identifier] = document
    if not result:
        raise FleetError(f"empty-registry:{relative}")
    return result


def source_form(document: dict) -> dict:
    return {key: value for key, value in document.items() if key != "_source"}


def validate_ref_list(document: dict, field: str) -> None:
    values = document.get(field, [])
    if not isinstance(values, list) or any(
            not isinstance(value, str) or not REF_RE.fullmatch(value)
            for value in values):
        raise FleetError(f"invalid-reference-list:{document.get('id')}:{field}")


def repository_root(root: Path) -> Path:
    """Resolve the checkout that owns a fleet registry.

    Payload sources are repository-relative so a composition never depends on
    the caller's working directory.  A copied synthetic registry is allowed to
    reach validation failures before this is needed, but a real composition
    must always live inside a checkout.
    """
    for candidate in (root, *root.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    raise FleetError(f"repository-root-not-found:{root}")


def payload_inventory(overlay: dict, checkout: Path, target: str) -> list[dict]:
    sources = list(overlay.get("payload_sources") or [])
    target_sources = overlay.get("payload_target_sources", {})
    if target_sources:
        sources.extend(target_sources.get(target, []))
    if not isinstance(sources, list) or not sources:
        raise FleetError(f"overlay-without-payload:{overlay['id']}")
    if any(not isinstance(value, str) or not value for value in sources):
        raise FleetError(f"invalid-payload-source:{overlay['id']}")
    files: dict[str, Path] = {}
    for source in sources:
        relative = Path(source)
        if relative.is_absolute() or ".." in relative.parts:
            raise FleetError(f"unsafe-payload-source:{overlay['id']}:{source}")
        resolved = (checkout / relative).resolve()
        try:
            resolved.relative_to(checkout)
        except ValueError as exc:
            raise FleetError(f"unsafe-payload-source:{overlay['id']}:{source}") from exc
        if not resolved.exists():
            raise FleetError(f"missing-payload-source:{overlay['id']}:{source}")
        candidates = [resolved] if resolved.is_file() else sorted(resolved.rglob("*"))
        for candidate in candidates:
            if candidate.is_symlink():
                raise FleetError(f"payload-symlink:{overlay['id']}:{candidate}")
            if not candidate.is_file() or "__pycache__" in candidate.parts or candidate.suffix == ".pyc":
                continue
            path = candidate.relative_to(checkout).as_posix()
            files[path] = candidate
    if not files:
        raise FleetError(f"empty-payload:{overlay['id']}")
    return [{
        "path": path,
        "bytes": files[path].stat().st_size,
        "sha256": sha256_bytes(files[path].read_bytes()),
    } for path in sorted(files)]


def validate_registry(releases: dict[str, dict], hardware: dict[str, dict],
                      peripherals: dict[str, dict], overlays: dict[str, dict],
                      devices: dict[str, dict]) -> None:
    for release in releases.values():
        artifact = release.get("artifact", {})
        digest = artifact.get("sha256") if isinstance(artifact, dict) else None
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise FleetError(f"invalid-release-sha256:{release['id']}")
        if not isinstance(release.get("compatibility"), dict):
            raise FleetError(f"invalid-release-compatibility:{release['id']}")

    for profile in list(hardware.values()) + list(peripherals.values()):
        if not isinstance(profile.get("facts"), dict):
            raise FleetError(f"invalid-profile-facts:{profile['id']}")

    ownership: dict[tuple[str, str], list[tuple[str, set[str]]]] = {}
    for overlay in overlays.values():
        for field in ("compatible_releases", "dependencies", "targets",
                      "owns", "tests", "secret_refs"):
            validate_ref_list(overlay, field)
        if not overlay["compatible_releases"]:
            raise FleetError(f"overlay-without-release:{overlay['id']}")
        if not overlay["targets"]:
            raise FleetError(f"overlay-without-target:{overlay['id']}")
        if not overlay["owns"]:
            raise FleetError(f"overlay-without-ownership:{overlay['id']}")
        if not isinstance(overlay.get("owner"), str) or not overlay["owner"]:
            raise FleetError(f"overlay-without-owner:{overlay['id']}")
        if not isinstance(overlay.get("rollback_ref"), str) or not overlay["rollback_ref"]:
            raise FleetError(f"overlay-without-rollback:{overlay['id']}")
        if not isinstance(overlay.get("payload_sources"), list) or not overlay["payload_sources"]:
            raise FleetError(f"overlay-without-payload:{overlay['id']}")
        target_sources = overlay.get("payload_target_sources", {})
        if not isinstance(target_sources, dict) or any(
                target not in overlay["targets"] or not isinstance(values, list) or
                not values or any(not isinstance(value, str) or not value for value in values)
                for target, values in target_sources.items()):
            raise FleetError(f"invalid-payload-target-sources:{overlay['id']}")
        payload_status = overlay.get("payload_status", "incomplete")
        payload_blockers = overlay.get("payload_blockers", [])
        if payload_status not in {"incomplete", "complete"}:
            raise FleetError(f"invalid-payload-status:{overlay['id']}")
        if not isinstance(payload_blockers, list) or any(
                not isinstance(item, str) or not item for item in payload_blockers):
            raise FleetError(f"invalid-payload-blockers:{overlay['id']}")
        if payload_status == "complete" and payload_blockers:
            raise FleetError(f"complete-payload-has-blockers:{overlay['id']}")
        if payload_status == "incomplete" and not payload_blockers:
            raise FleetError(f"incomplete-payload-without-blockers:{overlay['id']}")
        if overlay.get("apply_strategy", "install") not in {
                "install", "preserve-and-verify", "render-and-install"}:
            raise FleetError(f"invalid-apply-strategy:{overlay['id']}")
        assertions = overlay.get("assertions", [])
        if not isinstance(assertions, list):
            raise FleetError(f"invalid-assertions:{overlay['id']}")
        for assertion in assertions:
            if not isinstance(assertion, dict) or not all(
                    isinstance(assertion.get(key), str) and assertion.get(key)
                    for key in ("authority", "key")) or "expected" not in assertion:
                raise FleetError(f"invalid-assertion:{overlay['id']}")
            if assertion.get("sensitive", False) is not False:
                raise FleetError(f"sensitive-assertion:{overlay['id']}:{assertion.get('key')}")
        if (payload_status == "complete" and
                overlay.get("apply_strategy", "install") == "preserve-and-verify" and
                not assertions):
            raise FleetError(f"preserve-overlay-without-assertions:{overlay['id']}")
        for release_id in overlay["compatible_releases"]:
            if release_id not in releases:
                raise FleetError(f"unknown-overlay-release:{overlay['id']}:{release_id}")
        for dependency in overlay["dependencies"]:
            if dependency not in overlays:
                raise FleetError(f"unknown-overlay-dependency:{overlay['id']}:{dependency}")
        for target in overlay["targets"]:
            if target not in devices:
                raise FleetError(f"unknown-overlay-target:{overlay['id']}:{target}")
        for resource in overlay["owns"]:
            key = (overlay["layer"], resource)
            targets = set(overlay["targets"])
            for existing, existing_targets in ownership.get(key, []):
                if targets & existing_targets:
                    raise FleetError(
                        f"ownership-conflict:{overlay['layer']}:{resource}:"
                        f"{existing}:{overlay['id']}")
            ownership.setdefault(key, []).append((overlay["id"], targets))
        for ref in overlay["secret_refs"]:
            if not REF_RE.fullmatch(ref) or "://" in ref:
                raise FleetError(f"invalid-secret-reference:{overlay['id']}:{ref}")

    for device in devices.values():
        state = device.get("lifecycle")
        if state not in LIFECYCLE_STATES:
            raise FleetError(f"invalid-lifecycle:{device['id']}:{state}")
        deployed = device.get("deployed")
        if not isinstance(deployed, bool):
            raise FleetError(f"invalid-deployed:{device['id']}")
        if state in ACTIVE_STATES and not deployed:
            raise FleetError(f"active-not-deployed:{device['id']}")
        if state == "candidate" and deployed:
            raise FleetError(f"candidate-deployed:{device['id']}")
        for registry, field in ((releases, "release"),
                                (hardware, "hardware_profile"),
                                (peripherals, "peripheral_profile")):
            if device.get(field) not in registry:
                raise FleetError(f"unknown-reference:{device['id']}:{field}")
        validate_ref_list(device, "overlays")
        validate_ref_list(device, "external_integrations")
        validate_ref_list(device, "secret_refs")
        if len(device["overlays"]) != len(set(device["overlays"])):
            raise FleetError(f"duplicate-device-overlay:{device['id']}")
        for overlay_id in device["overlays"]:
            overlay = overlays.get(overlay_id)
            if overlay is None:
                raise FleetError(f"unknown-overlay:{device['id']}:{overlay_id}")
            if device["id"] not in overlay["targets"]:
                raise FleetError(f"overlay-target-mismatch:{device['id']}:{overlay_id}")
            if device["release"] not in overlay["compatible_releases"]:
                raise FleetError(f"overlay-release-incompatible:{device['id']}:{overlay_id}")
            for dependency in overlay["dependencies"]:
                if dependency not in device["overlays"]:
                    raise FleetError(
                        f"missing-overlay-dependency:{device['id']}:"
                        f"{overlay_id}:{dependency}")
        for ref in device["secret_refs"]:
            if not REF_RE.fullmatch(ref) or "://" in ref:
                raise FleetError(f"invalid-secret-reference:{device['id']}:{ref}")


def order_overlays(device: dict, overlays: dict[str, dict]) -> list[str]:
    selected = set(device["overlays"])
    temporary: set[str] = set()
    permanent: set[str] = set()
    ordered: list[str] = []

    def visit(identifier: str) -> None:
        if identifier in permanent:
            return
        if identifier in temporary:
            raise FleetError(f"overlay-dependency-cycle:{device['id']}:{identifier}")
        temporary.add(identifier)
        for dependency in sorted(overlays[identifier]["dependencies"]):
            if dependency not in selected:
                raise FleetError(
                    f"missing-overlay-dependency:{device['id']}:"
                    f"{identifier}:{dependency}")
            visit(dependency)
        temporary.remove(identifier)
        permanent.add(identifier)
        ordered.append(identifier)

    for overlay_id in sorted(selected):
        visit(overlay_id)
    return ordered


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


def build_device(device: dict, releases: dict[str, dict],
                 hardware: dict[str, dict], peripherals: dict[str, dict],
                 overlays: dict[str, dict], checkout: Path) -> dict:
    ordered = order_overlays(device, overlays)
    sources = [
        releases[device["release"]],
        hardware[device["hardware_profile"]],
        peripherals[device["peripheral_profile"]],
        *[overlays[identifier] for identifier in ordered],
        device,
    ]
    source_hashes = {
        source["_source"]: sha256_bytes(canonical(source_form(source)))
        for source in sources
    }
    ownership = {
        f"{overlays[identifier]['layer']}:{resource}": {
            "layer": overlays[identifier]["layer"], "resource": resource,
            "owner": identifier}
        for identifier in ordered for resource in overlays[identifier]["owns"]
    }
    payloads = {
        identifier: payload_inventory(overlays[identifier], checkout, device["id"])
        for identifier in ordered
    }
    result = {
        "schema_version": SCHEMA_VERSION,
        "kind": "desired-composition",
        "device_id": device["id"],
        "hostname": device["hostname"],
        "room": device["room"],
        "lifecycle": device["lifecycle"],
        "deployed": device["deployed"],
        "channel": device["channel"],
        "release": device["release"],
        "hardware_profile": device["hardware_profile"],
        "peripheral_profile": device["peripheral_profile"],
        "overlays": ordered,
        "external_integrations": sorted(device["external_integrations"]),
        "secret_refs": sorted(set(
            device["secret_refs"] + [ref for identifier in ordered
                                      for ref in overlays[identifier]["secret_refs"]]
        )),
        "ownership": dict(sorted(ownership.items())),
        "payloads": payloads,
        "source_hashes": dict(sorted(source_hashes.items())),
    }
    result["composition_sha256"] = sha256_bytes(canonical(result))
    return result


def render_matrix(compositions: list[dict], hardware: dict[str, dict],
                  peripherals: dict[str, dict]) -> bytes:
    lines = [
        "# AsterTV release and composition matrix",
        "",
        "> Generated deterministically by `compile_fleet.py`; do not edit by hand.",
        "",
        "| Device | State | Channel | Release | Hardware / output | Overlays | Composition |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sorted(compositions, key=lambda value: value["device_id"]):
        hardware_label = hardware[item["hardware_profile"]]["label"]
        output = peripherals[item["peripheral_profile"]]["facts"].get("output_contract", "pending")
        overlays = "<br>".join(f"`{value}`" for value in item["overlays"]) or "none"
        lines.append(
            f"| {item['device_id']} | {item['lifecycle']}"
            f"{' / not deployed' if not item['deployed'] else ''} | {item['channel']} | "
            f"`{item['release']}` | {hardware_label}; {output} | {overlays} | "
            f"`{item['composition_sha256'][:12]}` |"
        )
    lines.extend(["", "## Boundaries", "",
                  "- Family retains its measured Dolby/HDR and equipment-control composition.",
                  "- Bedroom retains stereo and Wi-Fi stability requirements.",
                  "- Jen's 1080p-media/stereo limit belongs only to its hardware profile; native GUI resolution is permitted.",
                  "- Guest is a compiled candidate with no address, identity, firewall path or deployment.",
                  "- Opaque secret references identify custody only; no value appears in an output.", ""])
    return "\n".join(lines).encode()


def compile_fleet(root: Path, output_root: Path | None = None) -> list[dict]:
    root = root.resolve()
    output_root = (output_root or root).resolve()
    for schema in sorted((root / "schemas").glob("*.schema.json")):
        load_json_yaml(schema)
    fleet_source = root / "fleet.yaml"
    fleet = load_json_yaml(fleet_source)
    require(fleet, "fleet", ("id", "devices", "authority"), fleet_source)
    releases = load_directory(root, "releases", "release",
                              ("id", "artifact", "compatibility"))
    hardware = load_directory(root, "hardware", "hardware-profile",
                              ("id", "label", "facts"))
    peripherals = load_directory(root, "peripherals", "peripheral-profile",
                                 ("id", "label", "facts"))
    overlays = load_directory(root, "overlays", "overlay",
                              ("id", "owner", "layer", "compatible_releases",
                               "dependencies", "targets", "owns", "secret_refs",
                               "rollback_ref", "tests"))
    devices = load_directory(root, "devices", "device",
                             ("id", "hostname", "room", "lifecycle", "deployed",
                              "channel", "release", "hardware_profile",
                              "peripheral_profile", "overlays",
                              "external_integrations", "secret_refs"))
    validate_ref_list(fleet, "devices")
    if set(fleet["devices"]) != set(devices):
        raise FleetError("fleet-device-set-mismatch")
    validate_registry(releases, hardware, peripherals, overlays, devices)
    checkout = repository_root(root)
    compositions = [build_device(devices[identifier], releases, hardware,
                                 peripherals, overlays, checkout)
                    for identifier in sorted(devices)]
    for composition in compositions:
        atomic_write(output_root / "desired" / f"{composition['device_id']}.json",
                     json.dumps(composition, indent=2, sort_keys=True).encode() + b"\n")
    atomic_write(output_root / "reports" / "release-matrix.md",
                 render_matrix(compositions, hardware, peripherals))
    return compositions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parent)
    parser.add_argument("--output-root", type=Path)
    args = parser.parse_args(argv)
    try:
        compositions = compile_fleet(args.root, args.output_root)
    except FleetError as exc:
        parser.exit(2, f"fleet compilation failed: {exc}\n")
    print(json.dumps({
        "devices": len(compositions),
        "deployed": sum(1 for item in compositions if item["deployed"]),
        "candidates": sum(1 for item in compositions if not item["deployed"]),
        "outcome": "compiled",
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
