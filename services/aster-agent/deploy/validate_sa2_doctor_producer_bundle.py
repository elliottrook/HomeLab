#!/usr/bin/env python3
"""Validate the source-only SA2 fixed Doctor producer release packet."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("sa2-doctor-producer-manifest.json")
ENTRIES = {
    "/opt/aster-agent/doctor_incident_adapter.py": {
        "source": "services/aster-agent/doctor_incident_adapter.py",
        "sha256": "0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968",
        "predecessor_sha256": "c88c4e642426afff9718da79e89db5b8405f1a5c00fbcc0fa09c3ae5956272db",
    },
    "/opt/aster-agent/sysadmin_incident_store.py": {
        "source": "services/aster-agent/sysadmin_incident_store.py",
        "sha256": "5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328",
        "predecessor_sha256": "c1594faccb5eb86b557cdb07461b7b404754da628e4fb170103a1025a6678aeb",
    },
    "/opt/aster-agent/sysadmin_registered_producer.py": {
        "source": "services/aster-agent/sysadmin_registered_producer.py",
        "sha256": "3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a",
        "predecessor_sha256": "b4c7eb1e450795bfd43a1bf7f1c64a89cfb202260278926e74ebb9454dac6ecd",
    },
}
RUNTIME = {
    "target": "LXC104",
    "service": "aster-agent.service",
    "restart_required": True,
    "model_restart": False,
    "model_change": False,
    "automatic_routing": False,
    "observation_authority": "fixed-doctor-status-only",
    "repair_authority": False,
}


def _unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(), object_pairs_hook=_unique)
    if set(manifest) != {
        "schema_version", "release_id", "source_commit", "independent_source_review",
        "files", "runtime",
    } or manifest["schema_version"] != 1:
        raise ValueError("invalid release manifest shape")
    if (manifest["release_id"] != "sa2-fixed-doctor-status-producer-20261027"
            or manifest["source_commit"] != "c8346ed7ecaa4100ea819a89084608db4a8dc64d"
            or manifest["independent_source_review"] != "passed"
            or manifest["runtime"] != RUNTIME):
        raise ValueError("release boundary changed")
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != 3:
        raise ValueError("unexpected release file count")
    targets = set()
    for item in files:
        if not isinstance(item, dict) or set(item) != {
            "source", "target", "sha256", "predecessor_sha256",
        }:
            raise ValueError("invalid release file entry")
        if item["target"] in targets or item["target"] not in ENTRIES:
            raise ValueError("invalid or duplicate release target")
        targets.add(item["target"])
        if {key: item[key] for key in ("source", "sha256", "predecessor_sha256")} != ENTRIES[item["target"]]:
            raise ValueError("release source or predecessor mapping changed")
        if _digest(root / item["source"]) != item["sha256"]:
            raise ValueError("release source hash mismatch")
    if targets != set(ENTRIES):
        raise ValueError("release target set changed")
    return {"release_id": manifest["release_id"], "files": 3,
            "automatic_routing": False, "repair_authority": False}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
