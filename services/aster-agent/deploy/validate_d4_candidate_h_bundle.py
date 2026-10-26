#!/usr/bin/env python3
"""Validate the frozen, inactive D4 candidate-H staging bundle."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
MANIFEST = Path(__file__).with_name("d4-candidate-h-bundle-manifest.json")
SHA256 = re.compile(r"^[a-f0-9]{64}$")
MODE = re.compile(r"^0[0-7]{3}$")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(manifest_path: Path = MANIFEST, root: Path = ROOT) -> dict:
    data = json.loads(manifest_path.read_text())
    if set(data) != {
        "schema", "candidate", "candidate_source_commit", "activation",
        "identity", "packet", "output", "control_files", "service", "excluded",
    }:
        raise ValueError("manifest fields changed")
    if (
        data["schema"] != 1
        or data["candidate"] != "d4-candidate-h-unprivileged-v1"
        or data["candidate_source_commit"] != "0966af2d"
        or data["activation"] != "inactive-source-only"
    ):
        raise ValueError("candidate identity or activation changed")
    if data["identity"] != {
        "name": "aster-d4-eval", "uid": 977, "gid": 977,
        "shell": "/usr/sbin/nologin", "supplementary_groups": [],
    }:
        raise ValueError("dedicated identity boundary changed")

    packet = data["packet"]
    if packet != {
        "source_directory": "services/aster-agent/evals",
        "source_manifest": "services/aster-agent/evals/sa3-development-attempt-11-source-manifest.json",
        "source_manifest_sha256": "5e8b1ca0314fb3deefc9a45f9755f92947b7f14ca53c590e21a14ee50cce0414",
        "target_directory": "/var/lib/aster/d4-candidate-h",
        "directory_owner": "root", "directory_group": "aster-d4-eval",
        "directory_mode": "0750", "file_owner": "root",
        "file_group": "aster-d4-eval", "file_mode": "0640",
        "predecessor": "absent",
    }:
        raise ValueError("packet custody boundary changed")
    source_manifest = root / packet["source_manifest"]
    if digest(source_manifest) != packet["source_manifest_sha256"]:
        raise ValueError("packet source manifest digest mismatch")
    source_data = json.loads(source_manifest.read_text())
    if (
        source_data.get("schema") != "aster-sa3-development-source-manifest.v1"
        or source_data.get("candidate_alias") != "candidate-H"
        or source_data.get("authority") != "not-granted"
        or source_data.get("run_digest")
        != "423656a2336502f3a70de463b3e844b0e85c4bb74a59127cc8f70a0905ec31f4"
        or len(source_data.get("files", [])) != 11
    ):
        raise ValueError("packet source authority or file set changed")
    source_directory = root / packet["source_directory"]
    names = set()
    for entry in source_data["files"]:
        if set(entry) != {"name", "bytes", "sha256"}:
            raise ValueError("invalid packet source entry")
        path = source_directory / entry["name"]
        if (
            entry["name"] in names
            or not path.is_file()
            or path.is_symlink()
            or path.stat().st_size != entry["bytes"]
            or not SHA256.fullmatch(entry["sha256"])
            or digest(path) != entry["sha256"]
        ):
            raise ValueError(f"packet source mismatch: {entry['name']}")
        names.add(entry["name"])

    if data["output"] != {
        "target_directory": "/var/lib/aster/d4-candidate-h-output",
        "owner": "aster-d4-eval", "group": "aster-d4-eval", "mode": "0700",
        "must_be_empty": True, "predecessor": "absent",
    }:
        raise ValueError("output custody boundary changed")

    controls = data["control_files"]
    if not isinstance(controls, list) or len(controls) != 3:
        raise ValueError("exactly three control files required")
    targets = set()
    for entry in controls:
        if set(entry) != {
            "source", "source_sha256", "target", "owner", "group", "mode",
            "predecessor", "rollback",
        }:
            raise ValueError("invalid control entry")
        source = root / entry["source"]
        if (
            not source.is_file()
            or source.is_symlink()
            or not SHA256.fullmatch(entry["source_sha256"])
            or digest(source) != entry["source_sha256"]
            or not Path(entry["target"]).is_absolute()
            or not MODE.fullmatch(entry["mode"])
            or entry["owner"] != "root"
            or entry["group"] != "root"
            or entry["predecessor"] != "absent"
            or entry["rollback"] != "remove"
            or entry["target"] in targets
        ):
            raise ValueError(f"invalid control boundary: {entry.get('target')}")
        targets.add(entry["target"])
    if targets != {
        "/usr/local/libexec/aster-d4-candidate-h-launcher",
        "/etc/systemd/system/aster-d4-candidate-h.service",
        "/usr/lib/sysusers.d/aster-d4-eval.conf",
    }:
        raise ValueError("control target boundary changed")
    if data["service"] != {
        "name": "aster-d4-candidate-h.service",
        "must_remain_disabled": True, "must_remain_inactive": True,
    }:
        raise ValueError("service state boundary changed")
    if set(data["excluded"]) != {
        "credential-open", "journal-create", "model-call", "service-enable",
        "service-start", "supplementary-group-grant",
    }:
        raise ValueError("staging exclusions changed")
    return {
        "candidate": data["candidate"], "packet_files": len(names),
        "control_files": len(controls), "activation": data["activation"],
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
