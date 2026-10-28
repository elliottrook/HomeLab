#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("sa2-breadth-release-manifest.json")
EXPECTED_RUNTIME = {
    "target": "macOS publisher and LXC104",
    "aster_restart_count": 1,
    "enable_log_timer": True,
    "publish_fresh_doctor_catalogue": True,
    "model_restart": False,
    "model_change": False,
    "automatic_routing": False,
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


def validate(root: Path = ROOT, manifest_path: Path = MANIFEST) -> dict:
    value = json.loads(manifest_path.read_text(), object_pairs_hook=_unique)
    if set(value) != {"schema_version", "release_id", "mac_files", "lxc_files", "runtime"}:
        raise ValueError("invalid manifest shape")
    if value["schema_version"] != 1 or value["release_id"] != "sa2-breadth-evidence-20261028":
        raise ValueError("invalid release identity")
    if value["runtime"] != EXPECTED_RUNTIME:
        raise ValueError("runtime boundary changed")
    if len(value["mac_files"]) != 4 or len(value["lxc_files"]) != 9:
        raise ValueError("invalid release file count")
    seen = set()
    additions = 0
    for platform, items in (("mac", value["mac_files"]), ("lxc", value["lxc_files"])):
        for item in items:
            if set(item) != {"source", "target", "before_sha256", "after_sha256", "mode"}:
                raise ValueError("invalid release file shape")
            target = Path(item["target"])
            key = str(target)
            if not target.is_absolute() or key in seen:
                raise ValueError("unsafe or duplicate target")
            seen.add(key)
            if platform == "mac" and target.parent not in {
                Path("/Users/jelliott/lab/homelab/scripts"),
                Path("/Users/jelliott/lab/homelab/services/aster-agent"),
            }:
                raise ValueError("unexpected Mac target")
            if platform == "lxc" and target.parent not in {
                Path("/opt/aster-agent"), Path("/usr/local/libexec"), Path("/etc/systemd/system")
            }:
                raise ValueError("unexpected LXC target")
            if item["mode"] not in {"0644", "0755"}:
                raise ValueError("invalid mode")
            before = item["before_sha256"]
            if before is None:
                additions += 1
            elif not isinstance(before, str) or len(before) != 64:
                raise ValueError("invalid predecessor digest")
            source = root / item["source"]
            if digest(source) != item["after_sha256"]:
                raise ValueError("candidate source hash mismatch")
    if additions != 8:
        raise ValueError("invalid addition boundary")
    return {
        "release_id": value["release_id"],
        "manifest_sha256": digest(manifest_path),
        "mac_files": len(value["mac_files"]),
        "lxc_files": len(value["lxc_files"]),
        **value["runtime"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, separators=(",", ":")))
