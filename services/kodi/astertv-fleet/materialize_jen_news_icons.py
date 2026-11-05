#!/usr/bin/env python3
"""Materialize Jen's News icon overlay from its exact accepted base."""

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
SOURCE = CHECKOUT / "services/kodi/astertv-v3/m5"
BASE = SOURCE / "recovered/News.base.xml"
APPLY = SOURCE / "apply_jen_news_icons.py"
UNIT = SOURCE / "recovered/astertv-v3-m5n-jen.service"
BASE_SHA256 = "960645920dc25fd709c0310b178057afaae16fa5260404110b03fda98669cd77"
FINAL_SHA256 = "f9c4b4b9483908eb06a15ee9f126a60caceeedd8b6908cbb7af786b68cce9074"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_apply():
    spec = importlib.util.spec_from_file_location("astertv_m5n_apply", APPLY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, tuple[bytes, str, str]], dict]:
    base = BASE.read_bytes()
    if sha(base) != BASE_SHA256:
        raise RuntimeError("jen-news-base-drift")
    final = load_apply().patch_news(base)
    if sha(final) != FINAL_SHA256:
        raise RuntimeError("jen-news-render-drift")
    files = {
        "skin.asterhome/1080i/custom_1111_digest.xml":
            (final, "/storage/.kodi/addons/skin.asterhome/1080i/custom_1111_digest.xml", "0644"),
        "stable/News.base.xml":
            (base, "/storage/.aster-v3/m5n/News.base.xml", "0600"),
        "stable/apply_jen_news_icons.py":
            (APPLY.read_bytes(), "/storage/.aster-v3/m5n/apply_jen_news_icons.py", "0600"),
        "system.d/astertv-v3-m5n-jen.service":
            (UNIT.read_bytes(), "/storage/.config/system.d/astertv-v3-m5n-jen.service", "0644"),
    }
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-news-icons",
        "provenance": {
            "checkpoint": "astertv-v3-m5n-jen",
            "base_sha256": BASE_SHA256,
            "renderer": {"path": APPLY.relative_to(CHECKOUT).as_posix(),
                         "sha256": sha(APPLY.read_bytes())},
        },
        "files": [
            {"destination": destination, "bytes": len(data),
             "sha256": sha(data), "mode": mode}
            for _, (data, destination, mode) in sorted(files.items())
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, str, str]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, _, mode) in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, int(mode, 8)); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-news-icons")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
