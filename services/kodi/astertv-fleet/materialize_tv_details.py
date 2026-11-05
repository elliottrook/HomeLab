#!/usr/bin/env python3
"""Materialize the reconciled, provenance-bound AsterTV TV-details overlay."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
SOURCE = CHECKOUT / "services/kodi/astertv-v3/deploy/tv-details"
RECOVERED = SOURCE / "recovered"
INSTALL_ROOT = "/storage/.kodi/addons/"

FILES = {
    "script.asterruntime/aster-series-preview24/default.py": RECOVERED / "default.py",
    "script.asterruntime/aster-series-preview24/resources/lib/series_seerr_client.py": RECOVERED / "series_seerr_client.py",
    "script.asterruntime/aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml": SOURCE / "aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml",
    "script.asterruntime/aster-series-preview24/v3_series_extension.py": SOURCE / "aster-series-preview24/v3_series_extension.py",
    "script.asterruntime/aster-series-preview24/manifest.json": RECOVERED / "manifest.json",
    "skin.asterhome/tools/aster_v2_series.py": RECOVERED / "aster_v2_series.py",
    "skin.asterhome/media/player-controls/trailer.png": SOURCE / "skin.asterhome/media/player-controls/trailer.png",
    "skin.asterhome/media/ui-button-current-gold-rim.png": SOURCE / "skin.asterhome/media/ui-button-current-gold-rim.png",
    "skin.asterhome/media/ui-button-focus-gold-rim.png": SOURCE / "skin.asterhome/media/ui-button-focus-gold-rim.png",
    "plugin.video.astersearch/addon.xml": SOURCE / "plugin.video.astersearch/addon.xml",
    "plugin.video.astersearch/actor_search.py": SOURCE / "plugin.video.astersearch/actor_search.py",
    "plugin.video.astersearch/default.py": SOURCE / "plugin.video.astersearch/default.py",
}

EXPECTED = {
    "script.asterruntime/aster-series-preview24/default.py": "f81658e70630ed5c4b8c6e995b073be6c8287faabf5127fac8c1335fbbff720a",
    "script.asterruntime/aster-series-preview24/resources/lib/series_seerr_client.py": "26615b4ca67745d60fd1ce60517fb4d4f2908407c4d2e44a40c4194c741e8c33",
    "script.asterruntime/aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml": "cf708381d77b137e17036b44899dca5ce352c7b7dd52efc935875c1b08d07a7d",
    "script.asterruntime/aster-series-preview24/v3_series_extension.py": "c4c183c0ada6f7b7152760b78d837e01d39f546a0ec8491c253949138ecaf111",
    "script.asterruntime/aster-series-preview24/manifest.json": "aa589c8939b627aa19f9ec9b7abf9a0852eb3b33595b8c884e2b56f8ddb2dba0",
    "skin.asterhome/tools/aster_v2_series.py": "79522aa5a816067b174ae932fbb7740a0aeccb84fde6443ee0b209cfaacb0b18",
    "skin.asterhome/media/player-controls/trailer.png": "b2d7d331f02ddbced8c5eb875c43d3d9a0bdcf1c758cd9e4369ed38392730c71",
    "skin.asterhome/media/ui-button-current-gold-rim.png": "cbaf368d835e864e68ba816c9184350d59a9c0a861e1de9b6e8e03b6bb955925",
    "skin.asterhome/media/ui-button-focus-gold-rim.png": "c1de42c5d178eeb0c2136781f891c9543fea78a9a41c4a084a78d8fbc86f214f",
    "plugin.video.astersearch/addon.xml": "80ab9ffde1a06e3938825a37751aa0b1efbd8ac0dc8863bc438124938c3cdd85",
    "plugin.video.astersearch/actor_search.py": "3af636f47623514d69e3aa8480a0de91f048eeb629c029fc8cc2d486b515a39c",
    "plugin.video.astersearch/default.py": "6353c1473f25bd6b46fb37894e01ed101c89771f32dbf352d145debc9bcf97aa",
}

RENDERERS = (
    "deploy.py", "hotfix_dynamic_lists.py", "hotfix_episode_art.py",
    "hotfix_tv_connections.py", "hotfix_trailer_icon.py",
    "hotfix_series_cache_bounds.py", "hotfix_series_cache_limit.py",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def render() -> tuple[dict[str, bytes], dict]:
    lineage = json.loads((RECOVERED / "lineage.json").read_text())
    if lineage.get("kind") != "astertv-recovered-transform-lineage":
        raise RuntimeError("lineage-schema")
    if [row.get("renderer") for row in lineage.get("stages", [])] != list(RENDERERS):
        raise RuntimeError("lineage-stage-order")
    files = {destination: source.read_bytes() for destination, source in FILES.items()}
    for destination, data in files.items():
        if sha(data) != EXPECTED[destination]:
            raise RuntimeError("source-drift:" + destination)
    renderer_rows = []
    for name in RENDERERS:
        path = SOURCE / name
        renderer_rows.append({
            "path": path.relative_to(CHECKOUT).as_posix(),
            "sha256": sha(path.read_bytes()),
        })
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "tv-details-v3",
        "base_release": lineage["base_release"],
        "provenance": {
            "lineage": (RECOVERED / "lineage.json").relative_to(CHECKOUT).as_posix(),
            "checkpoint_host": lineage["checkpoint_host"],
            "independent_final_match_host": lineage["independent_final_match_host"],
            "renderers": renderer_rows,
        },
        "files": [
            {
                "path": destination,
                "destination": INSTALL_ROOT + destination,
                "bytes": len(files[destination]),
                "sha256": EXPECTED[destination],
                "mode": "0644",
            }
            for destination in sorted(files)
        ],
        "mutable_state": [
            {
                "destination": INSTALL_ROOT + "script.asterruntime/family-manifest.json",
                "reason": "shared composition manifest; preserve and verify component pin",
            },
            {
                "authority": "kodi",
                "key": "addon.enabled.plugin.video.astersearch",
                "reason": "Kodi addon database state is asserted after installation",
            },
        ],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, bytes], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for destination, data in files.items():
        target = output / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, 0o644)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/tv-details-v3")
    args = parser.parse_args(argv)
    files, manifest = render()
    write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
