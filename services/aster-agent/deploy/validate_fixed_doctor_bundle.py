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
        "database", "dependencies", "services", "excluded",
    }:
        raise ValueError("manifest fields changed")
    if data["schema"] != 1 or data["activation"] != "target-shape-only":
        raise ValueError("bundle must remain a target-shape-only schema-1 candidate")
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
    expected_targets = {
        ("mac-mini", "/Users/jelliott/lab/homelab/scripts/build-aster-health-report.py"),
        ("mac-mini", "/Users/jelliott/lab/homelab/scripts/scheduled-report.sh"),
        ("lxc104", "/opt/homelab-broker/broker_admin.py"),
        ("lxc104", "/opt/homelab-broker/broker_service.py"),
        ("lxc104", "/opt/aster-agent/fixed_doctor_caller.py"),
        ("lxc104", "/opt/aster-agent/fixed_doctor_gateway.py"),
        ("lxc104", "/opt/aster-agent/fixed_doctor_capability.py"),
        ("lxc104", "/opt/aster-agent/doctor_model_projection.py"),
        ("lxc104", "/opt/aster-agent/doctor_structured_incident_adapter.py"),
        ("lxc104", "/etc/systemd/system/aster-fixed-doctor-caller.service"),
        ("lxc104", "/etc/systemd/system/aster-fixed-doctor-gateway.service"),
        ("lxc104", "/usr/lib/sysusers.d/aster-fixed-doctor.conf"),
    }
    if seen_targets != expected_targets:
        raise ValueError("target path boundary changed")
    if data["database"] != {
        "host": "lxc104", "path": "/var/lib/homelab-broker/broker.db",
        "checkpoint_before_enrollment": True, "enrollment_is_separate": True,
    }:
        raise ValueError("database boundary changed")
    dependencies = data["dependencies"]
    if (not isinstance(dependencies, list) or len(dependencies) != 3 or
            any(not isinstance(item, dict) or set(item) != {"host", "target", "sha256"}
                for item in dependencies)):
        raise ValueError("dependency boundary changed")
    dependency_targets = set()
    for item in dependencies:
        if (item["host"] != "lxc104" or not Path(item["target"]).is_absolute() or
                not SHA256.fullmatch(item["sha256"]) or item["target"] in dependency_targets):
            raise ValueError("invalid dependency pin")
        dependency_targets.add(item["target"])
    if dependency_targets != {
        "/opt/aster-agent/doctor_incident_adapter.py",
        "/opt/aster-agent/sysadmin_investigation.py",
        "/opt/homelab-broker/broker_core.py",
    }:
        raise ValueError("dependency boundary changed")
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
