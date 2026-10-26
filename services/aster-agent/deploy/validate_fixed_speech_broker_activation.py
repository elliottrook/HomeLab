#!/usr/bin/env python3
"""Validate the exact fixed Speech broker activation packet."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("fixed-speech-broker-activation-manifest.json")
SHA = re.compile(r"^[a-f0-9]{64}$")


def validate(path: Path = MANIFEST, root: Path = ROOT) -> dict[str, object]:
    data = json.loads(path.read_text())
    if set(data) != {"schema", "candidate", "source_commit", "runner", "entries", "dependencies", "database", "activation", "rollback", "excluded"}:
        raise ValueError("manifest fields changed")
    if data["schema"] != 1 or data["candidate"] != "d4-fixed-speech-broker-v2":
        raise ValueError("candidate identity changed")
    runner = data["runner"]
    runner_source = root / runner.get("source", "")
    if (set(runner) != {"source", "sha256", "checkpoint", "socket_wait_seconds", "database_restore_owner", "database_restore_mode"} or
            not runner_source.is_file() or hashlib.sha256(runner_source.read_bytes()).hexdigest() != runner.get("sha256") or
            runner.get("checkpoint") != "/var/lib/homelab-broker/fixed-speech-pre-activation-20261026-r1" or
            runner.get("socket_wait_seconds") != 5 or runner.get("database_restore_owner") != "hlabroker:hlabroker" or
            runner.get("database_restore_mode") != "0600"):
        raise ValueError("runner boundary changed")
    entries = data["entries"]
    if not isinstance(entries, list) or len(entries) != 2:
        raise ValueError("exactly two broker replacements are required")
    expected = {
        "/opt/homelab-broker/broker_admin.py": "0700",
        "/opt/homelab-broker/broker_service.py": "0644",
    }
    for item in entries:
        if set(item) != {"source", "target", "source_sha256", "predecessor_sha256", "owner", "group", "mode"}:
            raise ValueError("entry fields changed")
        source = root / item["source"]
        if (item["target"] not in expected or item["mode"] != expected[item["target"]] or
                item["owner"] != "root" or item["group"] != "root" or
                not SHA.fullmatch(item["predecessor_sha256"]) or
                hashlib.sha256(source.read_bytes()).hexdigest() != item["source_sha256"]):
            raise ValueError("entry boundary changed")
    if {item["target"] for item in entries} != set(expected):
        raise ValueError("target set changed")
    if data["dependencies"] != [
        {"target": "/opt/homelab-broker/broker_core.py", "sha256": "2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99"},
        {"target": "/etc/systemd/system/homelab-broker.service", "sha256": "8a65bb18cba169df4ab9a0b72c0f5fa04cbd9b6ddc75ade66ca3bef4c80aa1f3"},
    ]:
        raise ValueError("dependency boundary changed")
    if data["database"] != {
        "path": "/var/lib/homelab-broker/broker.db", "checkpoint_before_change": True,
        "required_absent_capability": "diagnostic.aster-speech.latest",
        "required_existing_capability": "diagnostic.aster-inference.latest",
    }:
        raise ValueError("database boundary changed")
    if data["activation"] != {
        "agent": "agent-aster-fixed-speech", "agent_uid": 975,
        "service": "aster-fixed-speech", "capability": "diagnostic.aster-speech.latest",
        "risk": "green", "probation_allowed": False,
        "units": ["aster-fixed-speech-gateway.service", "aster-fixed-speech-caller.service"],
        "broker_restart_limit": 1, "canary_calls": 1,
    }:
        raise ValueError("activation boundary changed")
    if data["rollback"] != {
        "stop_candidate_units": True, "restore_database_checkpoint": True,
        "restore_predecessor_files": True, "broker_restart_limit": 1,
    }:
        raise ValueError("rollback boundary changed")
    required_exclusions = {"aster-agent-restart", "host-reboot", "model-call", "repair", "automatic-routing", "other-capability-change", "schedule-change", "git-push"}
    if set(data["excluded"]) != required_exclusions:
        raise ValueError("exclusions changed")
    return {"candidate": data["candidate"], "replacements": 2, "canary_calls": 1}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
