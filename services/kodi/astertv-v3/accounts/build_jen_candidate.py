#!/usr/bin/env python3
"""Build the deterministic, Jen-only M2 synthetic-account candidate."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import tarfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent
ADDON = ROOT / "addon/script.asterprofiles.v3lab"
SOURCES = {
    "addons/script.asterprofiles.v3lab/addon.xml": ADDON / "addon.xml",
    "addons/script.asterprofiles.v3lab/default.py": ADDON / "default.py",
    "addons/script.asterprofiles.v3lab/service.py": ADDON / "service.py",
    "addons/script.asterprofiles.v3lab/registry.py": ROOT / "registry.py",
    "addons/script.asterprofiles.v3lab/access_policy.py": ROOT / "access_policy.py",
    "addons/script.asterprofiles.v3lab/synthetic-fixture.json": ROOT / "synthetic-fixture.json",
    "keymaps/z-astertv-v3-m2-profile-gate.xml": ROOT / "keymaps/z-astertv-v3-m2-profile-gate.xml",
}
SECRET = re.compile(
    rb"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret)"
    rb"\s*[:=]\s*['\"][^'\"\r\n]{4,}"
)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def validate_source(path, payload):
    if path.is_symlink() or not path.is_file():
        raise ValueError("candidate-source-missing-or-symlink:" + str(path))
    if b"-----BEGIN " in payload and (b"PRIVATE " + b"KEY-----") in payload:
        raise ValueError("private-key-in-candidate")
    if SECRET.search(payload):
        raise ValueError("credential-assignment-in-candidate")


def build_bytes():
    rows = []
    payloads = {}
    for name, path in sorted(SOURCES.items()):
        data = path.read_bytes()
        validate_source(path, data)
        payloads[name] = data
        rows.append({"path": name, "bytes": len(data), "sha256": digest(data)})
    manifest = {
        "schema": 1,
        "kind": "astertv-v3-m2-jen-synthetic-candidate",
        "target": "AsterTV-Jen",
        "release": False,
        "profile_namespace": "script.asterprofiles.v3lab",
        "production_service_mappings": False,
        "client_capability_policy_included": False,
        "rollback": "remove isolated addon and addon_data directories; accepted v2 files remain unchanged",
        "inputs": rows,
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(payloads.items()):
                info = tarfile.TarInfo("astertv-v3-m2-jen/" + name)
                info.size = len(data); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
                archive.addfile(info, io.BytesIO(data))
            info = tarfile.TarInfo("astertv-v3-m2-jen/manifest.json")
            info.size = len(encoded); info.mode = 0o644; info.mtime = 0; info.uid = 0; info.gid = 0
            archive.addfile(info, io.BytesIO(encoded))
    return buffer.getvalue()


def validate_archive(payload):
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        members = archive.getmembers()
        for member in members:
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or ".." in path.parts:
                raise ValueError("unsafe-candidate-member")
        manifest = json.load(archive.extractfile("astertv-v3-m2-jen/manifest.json"))
        by_name = {member.name: member for member in members}
        for row in manifest["inputs"]:
            name = "astertv-v3-m2-jen/" + row["path"]
            data = archive.extractfile(by_name[name]).read()
            if len(data) != row["bytes"] or digest(data) != row["sha256"]:
                raise ValueError("candidate-member-drift:" + row["path"])
        if manifest["target"] != "AsterTV-Jen" or manifest["release"]:
            raise ValueError("candidate-boundary-failed")
        if manifest["client_capability_policy_included"]:
            raise ValueError("client-capability-policy-must-remain-separate")
        return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_bytes()
    validate_archive(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name("." + args.output.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, args.output)
    print(json.dumps({"output": str(args.output), "bytes": len(payload), "sha256": digest(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
