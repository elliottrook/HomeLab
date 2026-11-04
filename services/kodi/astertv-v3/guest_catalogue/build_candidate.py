#!/usr/bin/env python3
"""Build the reproducible Jen-only Guest catalogue/playback candidate."""

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
ACCOUNTS = ROOT.parent / "accounts"
PROFILE = ACCOUNTS / "addon/script.asterprofiles.v3lab"
GUEST = ROOT / "addon/plugin.video.asterguest"
SOURCES = {}
for path in sorted(PROFILE.iterdir()):
    if path.is_file():
        SOURCES["addons/script.asterprofiles.v3lab/" + path.name] = path
for name in ("registry.py", "access_policy.py", "authority.py", "identity_resolver.py",
             "synthetic-fixture.json"):
    SOURCES["addons/script.asterprofiles.v3lab/" + name] = ACCOUNTS / name
for path in sorted(GUEST.iterdir()):
    if path.is_file():
        SOURCES["addons/plugin.video.asterguest/" + path.name] = path
SOURCES["keymaps/z-astertv-v3-m2-profile-gate.xml"] = (
    ACCOUNTS / "keymaps/z-astertv-v3-m2-profile-gate.xml"
)
SECRET = re.compile(
    rb"(?i)(?:password|passwd|api[_ -]?key|access[_ -]?token|client[_ -]?secret)"
    rb"\s*[:=]\s*['\"][^'\"\r\n]{8,}"
)


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def build_bytes():
    rows = []; payloads = {}
    for name, path in sorted(SOURCES.items()):
        data = path.read_bytes()
        if path.is_symlink() or not path.is_file() or SECRET.search(data):
            raise ValueError("unsafe-candidate-source:" + str(path))
        payloads[name] = data
        rows.append({"path": name, "bytes": len(data), "sha256": digest(data)})
    manifest = {
        "schema": 1, "kind": "astertv-v3-m2-jen-guest-playback-candidate",
        "target": "AsterTV-Jen", "release": False,
        "production_clients": False, "source_identity": "AsterTV-Guest",
        "allowed_libraries": ["Movies", "Shows", "Archive Movies", "Archive TV"],
        "client_capability_policy_included": False,
        "inputs": rows,
    }
    encoded = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w") as archive:
            for name, data in sorted(payloads.items()):
                info = tarfile.TarInfo("astertv-v3-m2-jen-guest/" + name)
                info.size = len(data); info.mode = 0o644; info.mtime = 0
                info.uid = info.gid = 0
                archive.addfile(info, io.BytesIO(data))
            info = tarfile.TarInfo("astertv-v3-m2-jen-guest/manifest.json")
            info.size = len(encoded); info.mode = 0o644; info.mtime = 0
            info.uid = info.gid = 0
            archive.addfile(info, io.BytesIO(encoded))
    return buffer.getvalue()


def validate(payload):
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            path = PurePosixPath(member.name)
            if not member.isfile() or path.is_absolute() or ".." in path.parts:
                raise ValueError("unsafe-candidate-member")
        manifest = json.load(archive.extractfile(
            "astertv-v3-m2-jen-guest/manifest.json"
        ))
        if (manifest["target"] != "AsterTV-Jen" or manifest["release"]
                or manifest["production_clients"]):
            raise ValueError("candidate-boundary")
        return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = build_bytes(); validate(payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_name("." + args.output.name + ".tmp")
    temporary.write_bytes(payload); os.replace(temporary, args.output)
    print(json.dumps({"output": str(args.output), "bytes": len(payload),
                      "sha256": digest(payload)}, sort_keys=True))


if __name__ == "__main__":
    main()
