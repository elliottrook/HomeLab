#!/usr/bin/env python3
"""Materialize Jen's immutable Aster client without identity or key state."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/aster_client/addon/script.astertv.voice"
INSTALL_ROOT = "/storage/.kodi/addons/script.astertv.voice/"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, bytes], dict]:
    files = {
        path.relative_to(SOURCE).as_posix(): path.read_bytes()
        for path in sorted(SOURCE.rglob("*")) if path.is_file() and not path.is_symlink()
    }
    if "addon.xml" not in files or "default.py" not in files:
        raise RuntimeError("jen-aster-client-source-incomplete")
    rows = [
        {"destination": INSTALL_ROOT + relative, "bytes": len(data),
         "sha256": sha(data), "mode": "0644"}
        for relative, data in sorted(files.items())
    ]
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-aster-client",
        "source": {"path": SOURCE.relative_to(CHECKOUT).as_posix()},
        "files": rows,
        "dependencies": ["jen-account-registry"],
        "mutable_state": [
            {"path": "/storage/.aster-private/astertv-broker.key",
             "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/profiles.json",
             "bundled": False, "sensitive": True, "owner": "jen-account-registry"},
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/authority.json",
             "bundled": False, "sensitive": True, "owner": "jen-account-registry"},
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, bytes], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, data in sorted(files.items()):
        target = output / "script.astertv.voice" / relative
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
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-aster-client")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
