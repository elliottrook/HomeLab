#!/usr/bin/env python3
"""Materialize the Family restart overlay from the pinned v2.0.7 archive."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKOUT = HERE.parents[2]
TRANSFORMER = CHECKOUT / "services/kodi/astertv-v2/reconciliation/apply_family_restart_button.py"
RELEASE = HERE / "releases/astertv-v2.0.7-2026-10-31.yaml"
MEMBERS = {
    "settings": "aster-v2-package/lab-addon-snapshot/skin.asterhome/1080i/Settings.xml",
    "dispatch": "aster-v2-package/lab-addon-snapshot/skin.asterhome/tools/select_dispatch.py",
    "family": "aster-v2-package/lab-addon-snapshot/script.asterruntime/family-manifest.json",
}
DESTINATIONS = {
    "settings": "skin.asterhome/1080i/Settings.xml",
    "dispatch": "skin.asterhome/tools/select_dispatch.py",
    "helper": "skin.asterhome/tools/restart_astertv.py",
    "family": "script.asterruntime/family-manifest.json",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def load_transformer():
    spec = importlib.util.spec_from_file_location("astertv_family_restart_transformer", TRANSFORMER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def transform(archive: Path) -> tuple[dict[str, bytes], dict]:
    release = json.loads(RELEASE.read_text())
    archive_bytes = archive.read_bytes()
    if sha(archive_bytes) != release["artifact"]["sha256"]:
        raise RuntimeError("base-release-hash")
    with tarfile.open(archive, "r:gz") as source:
        original = {name: source.extractfile(member).read() for name, member in MEMBERS.items()}
    module = load_transformer()
    for name, expected in module.EXPECTED.items():
        if sha(original[name]) != expected:
            raise RuntimeError("predecessor-hash:" + name)

    settings = original["settings"].decode()
    if settings.count("<ondown>200</ondown>") != 9:
        raise RuntimeError("settings-navigation-anchor")
    settings = settings.replace("<ondown>200</ondown>", "<ondown>208</ondown>")
    anchor = (
        '<control type="label"><left>145</left><top>990</top><width>1650</width>'
        '<height>34</height><label>Choose a settings area above · Left opens the '
        'navigation rail</label>'
    )
    restart = (
        '<control type="button" id="208"><left>145</left><top>900</top>'
        '<width>290</width><height>60</height><label>Restart AsterTV</label>'
        '<font>font20</font><align>center</align><aligny>center</aligny>'
        '<onleft>8999</onleft><onright>208</onright><onup>200</onup>'
        '<ondown>208</ondown><enable>!Player.HasMedia</enable>'
        '<onclick>RunScript(special://skin/tools/restart_astertv.py)</onclick>'
        '<textcolor>fff3eee5</textcolor><focusedcolor>fff3eee5</focusedcolor>'
        '<texturefocus border="20" colordiffuse="ff005c46">'
        'special://skin/media/ui-panel.png</texturefocus>'
        '<texturenofocus border="20" colordiffuse="f23b3a32">'
        'special://skin/media/ui-panel.png</texturenofocus></control>'
    )
    settings_bytes = module.replace_once(settings, anchor, restart + anchor, "restart-control").encode()
    dispatch = module.replace_once(
        original["dispatch"].decode(),
        "        203: 'ActivateWindow(AddonBrowser)',\n",
        "        203: 'ActivateWindow(AddonBrowser)',\n"
        "        208: 'RunScript(special://skin/tools/restart_astertv.py)',\n",
        "restart-dispatch",
    ).encode()
    helper = module.build_helper()
    family = json.loads(original["family"])
    family["skin"]["1080i/Settings.xml"] = sha(settings_bytes)
    family["skin"]["tools/select_dispatch.py"] = sha(dispatch)
    family["skin"]["tools/restart_astertv.py"] = sha(helper)
    outputs = {"settings": settings_bytes, "dispatch": dispatch,
               "helper": helper, "family": canonical(family)}
    manifest = {
        "schema_version": 1,
        "kind": "astertv-materialized-overlay",
        "id": "family-kodi-restart",
        "base_release": {"id": release["id"], "sha256": release["artifact"]["sha256"]},
        "renderer": {"path": TRANSFORMER.relative_to(CHECKOUT).as_posix(),
                     "sha256": sha(TRANSFORMER.read_bytes())},
        "outputs": [{"destination": DESTINATIONS[name], "bytes": len(data),
                     "sha256": sha(data), "mode": "0755" if name == "helper" else "0644"}
                    for name, data in sorted(outputs.items())],
    }
    return outputs, manifest


def write_tree(output: Path, outputs: dict[str, bytes], manifest: dict) -> None:
    output.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        target = output / DESTINATIONS[name]
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}-", dir=target.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(data); stream.flush(); os.fsync(stream.fileno())
            os.chmod(temporary, 0o755 if name == "helper" else 0o644)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    (output / "materialization-manifest.json").write_bytes(canonical(manifest))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=CHECKOUT / "services/kodi/dist/astertv-v2.0.7-release-2026-10-31.tar.gz")
    parser.add_argument("--output", type=Path, default=HERE / "materialized/family-kodi-restart")
    args = parser.parse_args(argv)
    outputs, manifest = transform(args.artifact)
    write_tree(args.output, outputs, manifest)
    print(json.dumps({"output": str(args.output), "files": len(outputs),
                      "manifest_sha256": sha(canonical(manifest))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
