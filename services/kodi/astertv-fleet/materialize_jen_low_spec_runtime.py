#!/usr/bin/env python3
"""Materialize Jen-only host gates and the low-spec Jellyfin policy."""

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
SOURCE = CHECKOUT / "services/kodi/astertv-v3/low-spec"
RECOVERED = SOURCE / "recovered/host-gates"
CHECKPOINT = SOURCE / "recovered/host-gates-manifest.json"
POLICY = SOURCE / "jellyfin_client_policy.py"
EXTERNALLY_OWNED = {
    "script.asterruntime/aster-global-search-ui22/movie.py": "jen-movie-youtube",
    "script.asterruntime/aster-series-preview24/default.py": "tv-details-v3",
    "skin.asterhome/tools/aster_v2_digest.py": "news-playback-v3",
    "skin.asterhome/tools/aster_v2_series.py": "tv-details-v3",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_policy():
    spec = importlib.util.spec_from_file_location("astertv_jen_low_spec_policy", POLICY)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, tuple[bytes, str, str]], dict]:
    checkpoint = json.loads(CHECKPOINT.read_text())
    if checkpoint.get("host") != "AsterTV-Jen" or len(checkpoint.get("files", {})) != 25:
        raise RuntimeError("jen-host-gate-checkpoint-drift")
    files = {}
    for relative, row in sorted(checkpoint["files"].items()):
        if relative in EXTERNALLY_OWNED:
            continue
        data = (RECOVERED / relative).read_bytes()
        if sha(data) != row["after_sha256"] or b"AsterTV-Jen" not in data:
            raise RuntimeError("jen-host-gate-output-drift:" + relative)
        files["host-gates/" + relative] = (
            data, "/storage/.kodi/addons/" + relative, "0755" if relative.endswith(".py") else "0644")
    if len(files) != 21:
        raise RuntimeError("jen-host-gate-ownership-count")
    policy = load_policy()
    files.update({
        "policy/jellyfin_client_policy.py":
            (POLICY.read_bytes(), "/storage/.aster-policy/jellyfin_client_policy.py", "0700"),
        "system.d/astertv-jen-jellyfin-policy.service":
            (policy.SERVICE.encode(), "/storage/.config/system.d/astertv-jen-jellyfin-policy.service", "0644"),
        "system.d/astertv-jen-jellyfin-policy.path":
            (policy.PATH_UNIT.encode(), "/storage/.config/system.d/astertv-jen-jellyfin-policy.path", "0644"),
    })
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "jen-low-spec-runtime",
        "provenance": {
            "checkpoint": "astertv-low-spec-host-gates-20261104",
            "checkpoint_sha256": sha(CHECKPOINT.read_bytes()),
            "excluded_outputs": EXTERNALLY_OWNED,
        },
        "files": [
            {"destination": destination, "bytes": len(data),
             "sha256": sha(data), "mode": mode}
            for _, (data, destination, mode) in sorted(files.items())
        ],
        "external_state": [
            {"path": "/storage/.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/helper/playutils.py",
             "expected_sha256": "e4715278558f7956030b92b34677dab71776cf7820f1787b1f68e8ff11d6d89b",
             "bundled": False, "sensitive": False},
            {"path": "/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/settings.xml",
             "bundled": False, "sensitive": True},
            {"authority": "jellyfin-server", "key": "arc-a380-hwa",
             "expected": "hevc-vp9-av1-mpeg2-decode:intel-vpp:on:opencl:off",
             "bundled": False, "sensitive": False},
        ],
        "mutable_state": [
            {"path": "/storage/.aster-policy/jellyfin-client-policy.json",
             "bundled": False, "sensitive": False},
            {"path": "/storage/.aster-policy/jellyfin-client-policy-status.json",
             "bundled": False, "sensitive": False},
            {"path": "/storage/.kodi/userdata/addon_data/plugin.video.jellyfin",
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
    parser.add_argument("--output", type=Path, default=HERE / "materialized/jen-low-spec-runtime")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
