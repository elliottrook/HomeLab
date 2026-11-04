#!/usr/bin/env python3
"""Repin only the reviewed AsterTV-Jen hostname adaptations."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import tempfile


ADDONS = Path("/storage/.kodi/addons")
RUNTIME = ADDONS / "script.asterruntime"
SKIN = ADDONS / "skin.asterhome"
HOST_GATE = Path("/storage/.aster-checkpoints/astertv-low-spec-host-gates-20261104/manifest.json")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-low-spec-runtime-repin-20261104")
COMPONENTS = (
    "aster-digest-player8",
    "aster-digest-reader6",
    "aster-global-search-ui22",
    "aster-network-preview6",
    "aster-series-preview24",
    "aster-video-scrub5",
)


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def atomic(path: Path, raw: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise SystemExit("AsterTV-Jen-root-only")
    if CHECKPOINT.exists():
        raise RuntimeError("runtime-repin-checkpoint-exists")
    if os.system("systemctl is-active --quiet kodi") == 0:
        raise RuntimeError("runtime-repin-requires-stopped-kodi")

    host_gate = json.loads(HOST_GATE.read_text())
    reviewed = host_gate.get("files", {})
    staged: dict[Path, bytes] = {}
    component_digests: dict[str, str] = {}

    for component in COMPONENTS:
        manifest_path = RUNTIME / component / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        changed = False
        for row in manifest.get("files", []):
            member = manifest_path.parent / row["path"]
            raw = member.read_bytes()
            relative = str(member.relative_to(ADDONS))
            current_sha = sha(raw)
            if row.get("sha256") == current_sha and row.get("bytes", len(raw)) == len(raw):
                continue
            evidence = reviewed.get(relative)
            if not evidence or evidence.get("after_sha256") != current_sha:
                raise RuntimeError("runtime-repin-unreviewed-drift:" + relative)
            row["sha256"] = current_sha
            if "bytes" in row:
                row["bytes"] = len(raw)
            changed = True
        if not changed:
            raise RuntimeError("runtime-repin-component-not-drifted:" + component)
        raw = encoded(manifest)
        staged[manifest_path] = raw
        component_digests[component] = sha(raw)

    digest_tool = SKIN / "tools/aster_v2_digest.py"
    raw = digest_tool.read_bytes()
    replacement = ("PIN = '" + component_digests["aster-digest-player8"] + "'").encode()
    updated, count = re.subn(rb"PIN = '[a-f0-9]{64}'", replacement, raw)
    if count != 1:
        raise RuntimeError("runtime-repin-digest-pin")
    compile(updated, str(digest_tool), "exec")
    staged[digest_tool] = updated

    series_tool = SKIN / "tools/aster_v2_series.py"
    raw = series_tool.read_bytes()
    replacement = ("MANIFEST_SHA='" + component_digests["aster-series-preview24"] + "'").encode()
    updated, count = re.subn(rb"MANIFEST_SHA='[a-f0-9]{64}'", replacement, raw)
    if count != 1:
        raise RuntimeError("runtime-repin-series-pin")
    compile(updated, str(series_tool), "exec")
    staged[series_tool] = updated

    family_path = RUNTIME / "family-manifest.json"
    family = json.loads(family_path.read_text())
    for component, digest in component_digests.items():
        family["components"][component]["manifest_sha256"] = digest
    for relative in tuple(family.get("skin", {})):
        path = SKIN / relative
        raw = staged.get(path, path.read_bytes())
        family["skin"][relative] = sha(raw)
    staged[family_path] = encoded(family)

    for path, raw in staged.items():
        if path.suffix == ".py":
            compile(raw, str(path), "exec")

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    report = {"host": "AsterTV-Jen", "files": {}, "components": component_digests}
    try:
        for path, updated in staged.items():
            original = path.read_bytes()
            saved = CHECKPOINT / "before" / path.relative_to(ADDONS)
            saved.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            saved.write_bytes(original)
            os.chmod(saved, 0o600)
            atomic(path, updated)
            report["files"][str(path.relative_to(ADDONS))] = {
                "before_sha256": sha(original), "after_sha256": sha(updated)}
        (CHECKPOINT / "manifest.json").write_bytes(encoded(report))
        os.chmod(CHECKPOINT / "manifest.json", 0o600)
    except Exception:
        for path in staged:
            saved = CHECKPOINT / "before" / path.relative_to(ADDONS)
            if saved.is_file():
                atomic(path, saved.read_bytes())
        raise
    print(json.dumps({"installed": True, "files": len(staged),
                      "components": len(component_digests)}, sort_keys=True))


if __name__ == "__main__":
    main()
