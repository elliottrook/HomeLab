#!/usr/bin/env python3
"""Validate the exact SA2 Doctor + SA3 candidate-E single-restart packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from validate_sa2_doctor_producer_bundle import validate as validate_sa2
from validate_sa3_proposal_gateway_bundle import validate as validate_sa3


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("sa2-sa3-composite-manifest.json")
EXPECTED_RUNTIME = {
    "target": "LXC104",
    "service": "aster-agent.service",
    "restart_count": 1,
    "model_restart": False,
    "model_change": False,
    "automatic_routing": False,
    "observation_authority": "fixed-doctor-status-only",
    "repair_authority": False,
}


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(), object_pairs_hook=_unique_object)
    if set(manifest) != {"schema_version", "release_id", "components", "runtime"}:
        raise ValueError("invalid composite manifest shape")
    if manifest["schema_version"] != 1 or manifest["release_id"] != "sa2-doctor-sa3-candidate-e-composite-20261027":
        raise ValueError("invalid composite identity")
    if manifest["runtime"] != EXPECTED_RUNTIME:
        raise ValueError("runtime authority boundary changed")
    components = manifest["components"]
    expected = {
        "sa2_manifest": "services/aster-agent/deploy/sa2-doctor-producer-manifest.json",
        "sa2_manifest_sha256": "d65cab046facf2dde8c985d15401362b8333ea98c35a058114622f488672c641",
        "sa3_manifest": "services/aster-agent/deploy/sa3-proposal-gateway-manifest.json",
        "sa3_manifest_sha256": "15bc75939c9659de104516930c1ac201d0ff423f8232953acb1f68655583fa82",
    }
    if components != expected:
        raise ValueError("component boundary changed")
    sa2_path = root / components["sa2_manifest"]
    sa3_path = root / components["sa3_manifest"]
    if _digest(sa2_path) != components["sa2_manifest_sha256"] or _digest(sa3_path) != components["sa3_manifest_sha256"]:
        raise ValueError("component manifest hash mismatch")
    sa2 = validate_sa2(root, sa2_path)
    sa3 = validate_sa3(root, sa3_path)
    return {
        "release_id": manifest["release_id"],
        "files": sa2["files"] + sa3["files"],
        "component_releases": [sa2["release_id"], sa3["release_id"]],
        "restart_count": 1,
        "automatic_routing": False,
        "repair_authority": False,
        "manifest_sha256": _digest(manifest_path),
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
