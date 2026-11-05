#!/usr/bin/env python3
"""Materialize Jen's immutable Guest catalogue adapter only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/guest_catalogue/addon/plugin.video.asterguest"
INSTALL_ROOT = "/storage/.kodi/addons/plugin.video.asterguest/"
POLICY_SHA256 = "451f4d2173743f5fab93e8ace1a43f7182fb91d1909bdb51651ed87245a7d1d0"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, bytes], dict]:
    files = {
        path.relative_to(SOURCE).as_posix(): path.read_bytes()
        for path in sorted(SOURCE.rglob("*")) if path.is_file() and not path.is_symlink()
    }
    if set(files) != {"addon.xml", "client.py", "core.py", "default.py", "service.py"}:
        raise RuntimeError("jen-guest-catalogue-source-drift")
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-guest-catalogue",
        "dependencies": ["jen-account-registry"],
        "files": [
            {"destination": INSTALL_ROOT + relative, "bytes": len(data),
             "sha256": sha(data), "mode": "0644"}
            for relative, data in sorted(files.items())
        ],
        "external_state": [
            {"path": "/storage/.aster-policy/jellyfin_client_policy.py",
             "sha256": POLICY_SHA256, "bundled": False, "sensitive": False},
        ],
        "mutable_state": [
            {"path": "/storage/.aster-private/jellyfin-guest.json",
             "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/addon_data/plugin.video.asterguest",
             "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab",
             "bundled": False, "sensitive": True, "owner": "jen-account-registry"},
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, bytes], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, data in sorted(files.items()):
        target = output / "plugin.video.asterguest" / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, 0o644); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-guest-catalogue")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
