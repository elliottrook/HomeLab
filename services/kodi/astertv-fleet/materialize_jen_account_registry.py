#!/usr/bin/env python3
"""Materialize Jen's immutable profile-authority code without profile state."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/accounts"
BUILDER_PATH = SOURCE / "build_jen_candidate.py"
INSTALL_ROOT = "/storage/.kodi/"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_builder():
    spec = importlib.util.spec_from_file_location("astertv_jen_account_builder", BUILDER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, bytes], dict]:
    builder = load_builder()
    files = {relative: source.read_bytes() for relative, source in builder.SOURCES.items()}
    expected = {row["path"]: row for row in
                builder.validate_archive(builder.build_bytes())["inputs"]}
    for relative, data in files.items():
        row = expected.get(relative)
        if row is None or row["bytes"] != len(data) or row["sha256"] != sha(data):
            raise RuntimeError("candidate-manifest-drift:" + relative)
    outputs = {}
    rows = []
    for relative, data in sorted(files.items()):
        destination = INSTALL_ROOT + relative
        outputs[relative] = data
        rows.append({"destination": destination, "bytes": len(data),
                     "sha256": sha(data), "mode": "0644"})
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-account-registry",
        "renderer": {"path": BUILDER_PATH.relative_to(CHECKOUT).as_posix(),
                     "sha256": sha(BUILDER_PATH.read_bytes())},
        "files": rows,
        "mutable_state": [
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/profiles.json", "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/addon_data/script.asterprofiles.v3lab/authority.json", "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/profiles.xml", "bundled": False, "sensitive": False},
        ],
    }
    return outputs, manifest


def write_tree(output: Path, files: dict[str, bytes], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, data in sorted(files.items()):
        target = output / relative
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
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-account-registry")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
