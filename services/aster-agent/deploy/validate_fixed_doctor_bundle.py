#!/usr/bin/env python3
"""Validate the frozen fixed-Doctor bundle without installing it."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("fixed-doctor-bundle-manifest.json")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
MODE = re.compile(r"^0[0-7]{3}$")


def validate(manifest_path: Path = MANIFEST, root: Path = ROOT) -> dict[str, int | str]:
    data = json.loads(manifest_path.read_text())
    if set(data) != {
        "schema", "candidate", "created_at", "activation", "entries",
        "database", "services", "excluded",
    }:
        raise ValueError("manifest fields changed")
    if data["schema"] != 1 or data["activation"] != "disabled":
        raise ValueError("bundle must remain a disabled schema-1 candidate")
    entries = data["entries"]
    if not isinstance(entries, list) or len(entries) != 12:
        raise ValueError("exactly twelve frozen files are required")
    seen_targets: set[tuple[str, str]] = set()
    replacements = additions = 0
    for entry in entries:
        common = {"host", "source", "target", "source_sha256", "mode", "owner", "group", "rollback"}
        if not common.issubset(entry) or set(entry) - common - {"predecessor", "predecessor_sha256"}:
            raise ValueError("invalid bundle entry fields")
        if entry["host"] not in {"mac-mini", "lxc104"}:
            raise ValueError("unexpected target host")
        source = root / entry["source"]
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"source is not a regular file: {entry['source']}")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if not SHA256.fullmatch(entry["source_sha256"]) or digest != entry["source_sha256"]:
            raise ValueError(f"source digest mismatch: {entry['source']}")
        if not Path(entry["target"]).is_absolute() or not MODE.fullmatch(entry["mode"]):
            raise ValueError("target and mode must be exact")
        key = (entry["host"], entry["target"])
        if key in seen_targets:
            raise ValueError("duplicate target")
        seen_targets.add(key)
        if entry["rollback"] == "restore":
            if set(entry) != common | {"predecessor_sha256"} or not SHA256.fullmatch(entry["predecessor_sha256"]):
                raise ValueError("replacement needs one pinned predecessor")
            replacements += 1
        elif entry["rollback"] == "remove":
            if set(entry) != common | {"predecessor"} or entry["predecessor"] != "absent":
                raise ValueError("addition must require an absent predecessor")
            additions += 1
        else:
            raise ValueError("unsupported rollback action")
    if replacements != 4 or additions != 8:
        raise ValueError("unexpected replacement/addition split")
    if data["database"] != {
        "host": "lxc104", "path": "/var/lib/homelab-broker/broker.db",
        "checkpoint_before_enrollment": True, "enrollment_is_separate": True,
    }:
        raise ValueError("database boundary changed")
    required_exclusions = {
        "launchagent-change", "service-start", "service-enable", "broker-restart",
        "database-enrollment", "capability-grant", "live-read", "model-route", "model-call",
    }
    if set(data["excluded"]) != required_exclusions:
        raise ValueError("staging exclusions changed")
    return {
        "candidate": data["candidate"], "files": len(entries),
        "replacements": replacements, "additions": additions,
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
