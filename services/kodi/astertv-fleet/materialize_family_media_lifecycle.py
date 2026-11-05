#!/usr/bin/env python3
"""Render the Family media-lifecycle client payload from its checkpoint."""

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
SOURCE = CHECKOUT / "services/kodi/astertv-v3/deploy/media-lifecycle"
RECOVERED = SOURCE / "recovered"
REPAIR_PATH = SOURCE / "repair.py"
INSTALL_ROOT = "/storage/.kodi/addons/"
INPUTS = {
    "plugin.video.asterhome__library.py": "plugin.video.asterhome/library.py",
    "skin.asterhome__tools__next_episode.py": "skin.asterhome/tools/next_episode.py",
    "script.asterruntime__aster-global-search-ui22__resources__lib__movie_player.py": "script.asterruntime/aster-global-search-ui22/resources/lib/movie_player.py",
    "script.asterruntime__aster-global-search-ui22__manifest.json": "script.asterruntime/aster-global-search-ui22/manifest.json",
    "script.asterruntime__family-manifest.json": "script.asterruntime/family-manifest.json",
}
EXPECTED_FINAL = {
    "plugin.video.asterhome/library.py": "fabba2745f5009f449b119af6a83a8b7139efcabc4f7a1570fb6cccf4db12045",
    "skin.asterhome/tools/next_episode.py": "875b413fa63b5fd618398824ec1ddf10d7a46822d7bd9ede20e6f40896cf5c6b",
    "script.asterruntime/aster-global-search-ui22/resources/lib/movie_player.py": "8970897a29c8160207d6e07cc391abbb932c1f566017514f0661a3618663512a",
    "script.asterruntime/aster-global-search-ui22/manifest.json": "08692c763ea23e807113f6c3aa8a83d801bd23553b8f1f4999dd2ac79e932b14",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_repair():
    spec = importlib.util.spec_from_file_location("astertv_family_media_renderer", REPAIR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def render() -> tuple[dict[str, bytes], dict]:
    repair = load_repair()
    path_map = {
        repair.LIBRARY: "plugin.video.asterhome__library.py",
        repair.NEXT: "skin.asterhome__tools__next_episode.py",
        repair.PLAYER: "script.asterruntime__aster-global-search-ui22__resources__lib__movie_player.py",
        repair.MANIFEST: "script.asterruntime__aster-global-search-ui22__manifest.json",
        repair.FAMILY: "script.asterruntime__family-manifest.json",
    }
    originals = {path: (RECOVERED / name).read_bytes() for path, name in path_map.items()}
    for path, expected in repair.EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("predecessor-drift:" + str(path))
    candidates = repair.candidates(originals)
    files = {
        INPUTS[path_map[path]]: data
        for path, data in candidates.items() if path != repair.FAMILY
    }
    if {path: sha(data) for path, data in files.items()} != EXPECTED_FINAL:
        raise RuntimeError("rendered-output-drift")
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "family-media-lifecycle",
        "renderer": {"path": REPAIR_PATH.relative_to(CHECKOUT).as_posix(),
                     "sha256": sha(REPAIR_PATH.read_bytes())},
        "checkpoint": "astertv-media-lifecycle-AsterTV-Family-20261105-031033",
        "files": [{"destination": INSTALL_ROOT + path, "bytes": len(data),
                   "sha256": sha(data), "mode": "0644"}
                  for path, data in sorted(files.items())],
        "external_artifact": "services/kodi/astertv-fleet/payload-definitions/family-intro-skipper.json",
        "mutable_state": [{
            "destination": INSTALL_ROOT + "script.asterruntime/family-manifest.json",
            "reason": "shared composition manifest; preserve and verify component relationship",
        }, {
            "authority": "jellyfin-server",
            "reason": "server plugin files and databases remain on TrueNAS and are asserted",
        }],
    }
    return files, manifest


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
    parser.add_argument("--output", type=Path, default=HERE / "materialized/family-media-lifecycle")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
