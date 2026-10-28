#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("sa1-sa3-forgejo-expansion-manifest.json")
EXPECTED_RUNTIME = {
    "target": "LXC104", "service": "aster-agent.service", "restart_count": 1,
    "model_restart": False, "model_change": False, "automatic_routing": False,
    "observation_authority": "fixed-registered-reports-and-status-only",
    "repair_authority": False,
}


def _unique(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST):
    value = json.loads(manifest_path.read_text(), object_pairs_hook=_unique)
    if set(value) != {"schema_version", "release_id", "files", "runtime"}:
        raise ValueError("invalid release manifest shape")
    if value["schema_version"] != 1 or value["release_id"] != "sa1-sa3-forgejo-expansion-20261028":
        raise ValueError("invalid release identity")
    if value["runtime"] != EXPECTED_RUNTIME:
        raise ValueError("runtime authority boundary changed")
    files = value["files"]
    if not isinstance(files, list) or len(files) != 5:
        raise ValueError("invalid release file count")
    targets = set()
    additions = 0
    for item in files:
        if set(item) != {"source", "target", "before_sha256", "after_sha256"}:
            raise ValueError("invalid release file shape")
        source = root / item["source"]
        target = Path(item["target"])
        if source.name != target.name or target.parent != Path("/opt/aster-agent") or target.name in targets:
            raise ValueError("unsafe or duplicate release target")
        targets.add(target.name)
        if item["before_sha256"] is None:
            additions += 1
        elif not isinstance(item["before_sha256"], str) or len(item["before_sha256"]) != 64:
            raise ValueError("invalid predecessor digest")
        if digest(source) != item["after_sha256"]:
            raise ValueError("candidate source hash mismatch")
    if additions != 1 or "forgejo_incident_adapter.py" not in targets:
        raise ValueError("invalid addition boundary")
    return {"release_id": value["release_id"], "files": files,
            "manifest_sha256": digest(manifest_path), **value["runtime"]}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
