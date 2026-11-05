#!/usr/bin/env python3
"""Render target-specific News playback outputs from accepted predecessors."""

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
SOURCE = CHECKOUT / "services/kodi/astertv-v3/deploy/news-playback"
RECOVERED = SOURCE / "recovered"
REPAIR_PATH = SOURCE / "repair.py"
TARGETS = {
    "astertv-family": {"host": "AsterTV-Family", "source": "astertv-family"},
    "astertv-jen": {"host": "AsterTV-Jen", "source": "astertv-jen"},
}
EXPECTED_FINAL = {
    "astertv-family": {
        "script.asterruntime/aster-digest-player8/resources/lib/digest_kodi_port.py": "98d9ce0678e29f878da16bfbde66229ae27504363955cda4cfe30e05c065b940",
        "script.asterruntime/aster-digest-player8/manifest.json": "b76c51bf34e536f16085b9d2a8114a2345326bd7e416603587c0b63d4324b534",
        "skin.asterhome/tools/aster_v2_digest.py": "fadb0466ec1c52df555c1f8ded1597bf85cf05b86610cf071440e3f360647b2d",
    },
    "astertv-jen": {
        "script.asterruntime/aster-digest-player8/resources/lib/digest_kodi_port.py": "98d9ce0678e29f878da16bfbde66229ae27504363955cda4cfe30e05c065b940",
        "script.asterruntime/aster-digest-player8/manifest.json": "665dac7b6941e61d3b82c64393c4c344c32c0fa925fb2549139259b35b52009d",
        "skin.asterhome/tools/aster_v2_digest.py": "5672e7c376d9559ba6acc78978865f9b7821027629cdc804a5b76488a73bc919",
    },
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_repair():
    spec = importlib.util.spec_from_file_location("astertv_news_playback_renderer", REPAIR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def predecessor(root: Path) -> dict[str, bytes]:
    return {
        "port": (root / "script.asterruntime/aster-digest-player8/resources/lib/digest_kodi_port.py").read_bytes(),
        "manifest": (root / "script.asterruntime/aster-digest-player8/manifest.json").read_bytes(),
        "family": (root / "script.asterruntime/family-manifest.json").read_bytes(),
        "wrapper": (root / "skin.asterhome/tools/aster_v2_digest.py").read_bytes(),
    }


def render() -> tuple[dict[str, tuple[bytes, int]], dict]:
    repair = load_repair()
    files: dict[str, tuple[bytes, int]] = {}
    rows = []
    lineage = []
    for device_id, target in sorted(TARGETS.items()):
        original = predecessor(RECOVERED / target["source"])
        expected = repair.BASELINES[target["host"]]
        for name, path in (("port", repair.PORT), ("manifest", repair.MANIFEST),
                           ("family", repair.FAMILY), ("wrapper", repair.WRAPPER)):
            if sha(original[name]) != expected[path]:
                raise RuntimeError(f"predecessor-drift:{device_id}:{name}")
        payload = repair.build_payload(original["port"], original["manifest"],
                                       original["family"], original["wrapper"])
        rendered = {
            "script.asterruntime/aster-digest-player8/resources/lib/digest_kodi_port.py": payload[repair.PORT],
            "script.asterruntime/aster-digest-player8/manifest.json": payload[repair.MANIFEST],
            "skin.asterhome/tools/aster_v2_digest.py": payload[repair.WRAPPER],
        }
        if {name: sha(data) for name, data in rendered.items()} != EXPECTED_FINAL[device_id]:
            raise RuntimeError("rendered-output-drift:" + device_id)
        for destination, data in sorted(rendered.items()):
            relative = f"targets/{device_id}/storage/.kodi/addons/{destination}"
            files[relative] = (data, 0o644)
            rows.append({"scope": device_id,
                         "destination": "/storage/.kodi/addons/" + destination,
                         "bytes": len(data), "sha256": sha(data), "mode": "0644"})
        lineage.append({"device_id": device_id, "host": target["host"],
                        "predecessors": {name: sha(data) for name, data in sorted(original.items())}})
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "news-playback-v3",
        "renderer": {"path": REPAIR_PATH.relative_to(CHECKOUT).as_posix(),
                     "sha256": sha(REPAIR_PATH.read_bytes())},
        "targets": sorted(TARGETS),
        "files": sorted(rows, key=lambda row: (row["scope"], row["destination"])),
        "lineage": lineage,
        "mutable_state": [{
            "destination": "/storage/.kodi/addons/script.asterruntime/family-manifest.json",
            "reason": "shared composition manifest; preserve and verify component relationship",
        }, {
            "destination": "/storage/.aster-release/news-playback-repair.json",
            "reason": "host-specific acceptance record generated after installation",
        }],
    }
    return files, manifest


def write_tree(output: Path, files: dict[str, tuple[bytes, int]], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for relative, (data, mode) in sorted(files.items()):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, mode); os.replace(temporary, target)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "materialized/news-playback-v3")
    args = parser.parse_args(argv)
    files, manifest = render(); write_tree(args.output, files, manifest)
    print(json.dumps({"output": str(args.output), "files": len(files),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
