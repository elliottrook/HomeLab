#!/usr/bin/env python3
"""Materialize Jen's podcast request UI while excluding private client state."""

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
SOURCE = CHECKOUT / "services/kodi/astertv-v3/podcast_requests"
ADDON = SOURCE / "addon/script.astertv.podcast.requests"
RECOVERED = SOURCE / "recovered"
APPLY = SOURCE / "apply_jen_podcast_requests.py"
BASE_INCLUDES = "0ba7ab639f0819fb057389c69652fd134e8330f08584bfe575c0a3874d58be4d"
BASE_PODCASTS = "70bb81dc58d3373ee434ca70b17b81c8823a41f27d51829891c8eba2f7ca7ee6"
FINAL_INCLUDES = "4173abc214531689026ccff0201f0c69115aefb77eacd646ffc8394eac66a4b7"
FINAL_PODCASTS = "2869213de3b3d7b5cc025ac4c3d36d70124ab5bec2b439e3a3290b5a5f9e0ea8"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_apply():
    spec = importlib.util.spec_from_file_location("astertv_m5p_apply", APPLY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, tuple[bytes, str, str]], dict]:
    module = load_apply()
    include_base = (RECOVERED / "IncludesBooks.base.xml").read_bytes()
    podcast_base = (RECOVERED / "custom_1120_podcasts.base.xml").read_bytes()
    if sha(include_base) != BASE_INCLUDES or sha(podcast_base) != BASE_PODCASTS:
        raise RuntimeError("jen-podcast-base-drift")
    include_final = module.patch_includes(include_base)
    podcast_final = module.patch_podcasts(podcast_base)
    if sha(include_final) != FINAL_INCLUDES or sha(podcast_final) != FINAL_PODCASTS:
        raise RuntimeError("jen-podcast-render-drift")
    files = {
        "skin.asterhome/1080i/IncludesBooks.xml":
            (include_final, "/storage/.kodi/addons/skin.asterhome/1080i/IncludesBooks.xml", "0644"),
        "skin.asterhome/1080i/custom_1120_podcasts.xml":
            (podcast_final, "/storage/.kodi/addons/skin.asterhome/1080i/custom_1120_podcasts.xml", "0644"),
        "stable/IncludesBooks.base.xml":
            (include_base, "/storage/.aster-v3/m5p/IncludesBooks.base.xml", "0600"),
        "stable/custom_1120_podcasts.base.xml":
            (podcast_base, "/storage/.aster-v3/m5p/custom_1120_podcasts.base.xml", "0600"),
        "stable/apply_jen_podcast_requests.py":
            (APPLY.read_bytes(), "/storage/.aster-v3/m5p/apply_jen_podcast_requests.py", "0600"),
        "system.d/astertv-v3-m5p-jen.service":
            ((RECOVERED / "astertv-v3-m5p-jen.service").read_bytes(),
             "/storage/.config/system.d/astertv-v3-m5p-jen.service", "0644"),
    }
    for source in sorted(ADDON.rglob("*")):
        if not source.is_file() or source.is_symlink():
            continue
        relative = source.relative_to(ADDON).as_posix()
        data = source.read_bytes()
        files["addon/script.astertv.podcast.requests/" + relative] = (
            data, "/storage/.kodi/addons/script.astertv.podcast.requests/" + relative, "0644")
        files["stable/script.astertv.podcast.requests/" + relative] = (
            data, "/storage/.aster-v3/m5p/script.astertv.podcast.requests/" + relative, "0600")
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-podcast-requests",
        "provenance": {
            "checkpoint": "astertv-v3-m5p-jen",
            "renderer": {"path": APPLY.relative_to(CHECKOUT).as_posix(),
                         "sha256": sha(APPLY.read_bytes())},
            "base_sha256": {"IncludesBooks.xml": BASE_INCLUDES,
                            "custom_1120_podcasts.xml": BASE_PODCASTS},
        },
        "files": [
            {"destination": destination, "bytes": len(data),
             "sha256": sha(data), "mode": mode}
            for _, (data, destination, mode) in sorted(files.items())
        ],
        "mutable_state": [
            {"path": "/storage/.kodi/userdata/addon_data/script.astertv.podcast.requests/client.json",
             "bundled": False, "sensitive": True},
            {"path": "/storage/.kodi/userdata/addon_data/script.astertv.podcast.requests/receipts.json",
             "bundled": False, "sensitive": True},
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
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-podcast-requests")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
