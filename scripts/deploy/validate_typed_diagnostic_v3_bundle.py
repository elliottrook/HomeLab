#!/usr/bin/env python3
"""Validate the frozen, inactive typed-diagnostic v3 source bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path(__file__).with_name("typed-diagnostic-v3-manifest.json")
TARGET_ROOT = Path("/Users/jelliott/lab/homelab")
EXPECTED = {
    TARGET_ROOT / "scripts/build-aster-health-report.py": ("replace", "0755", "restore"),
    TARGET_ROOT / "scripts/doctor.sh": ("replace", "0755", "restore"),
    TARGET_ROOT / "services/aster-agent/diagnostic_catalogue_v3.py": ("add", "0644", "remove"),
}
REQUIRED_EXCLUSIONS = {
    "launchagent_change", "schedule_change", "doctor_run", "catalogue_publish",
    "service_restart", "identity_change", "grant_change", "model_call",
    "automatic_route", "git_push",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(manifest_path: Path = MANIFEST) -> None:
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    if set(value) != {"schema", "source_commit", "files", "exclusions"} or value["schema"] != 1:
        raise ValueError("invalid manifest shape")
    if not isinstance(value["source_commit"], str) or len(value["source_commit"]) != 40:
        raise ValueError("invalid source commit")
    if set(value["exclusions"]) != REQUIRED_EXCLUSIONS:
        raise ValueError("invalid exclusions")
    files = value["files"]
    if not isinstance(files, list) or len(files) != len(EXPECTED):
        raise ValueError("invalid file count")
    seen: set[Path] = set()
    for item in files:
        if set(item) != {
            "action", "source", "target", "predecessor_sha256", "candidate_sha256",
            "owner", "group", "mode", "rollback",
        }:
            raise ValueError("invalid file entry")
        target = Path(item["target"])
        if target in seen or target not in EXPECTED:
            raise ValueError("duplicate or unexpected target")
        seen.add(target)
        action, mode, rollback = EXPECTED[target]
        if (item["action"], item["mode"], item["rollback"]) != (action, mode, rollback):
            raise ValueError("invalid action, mode or rollback")
        if item["owner"] != "jelliott" or item["group"] != "staff":
            raise ValueError("invalid custody")
        source = (ROOT / item["source"]).resolve()
        if ROOT.resolve() not in source.parents or not source.is_file():
            raise ValueError("invalid source")
        if digest(source) != item["candidate_sha256"]:
            raise ValueError("candidate drift")
        predecessor = item["predecessor_sha256"]
        if action == "replace" and (not isinstance(predecessor, str) or len(predecessor) != 64):
            raise ValueError("missing predecessor")
        if action == "add" and predecessor is not None:
            raise ValueError("addition has predecessor")
    if seen != set(EXPECTED):
        raise ValueError("missing target")


if __name__ == "__main__":
    validate()
    print("typed diagnostic v3 bundle: PASS")
