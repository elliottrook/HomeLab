#!/usr/bin/env python3
"""Finish Series visual acceptance without changing navigation or content."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
RUNTIME = ROOT / "script.asterruntime"
SERIES = RUNTIME / "aster-series-preview24"
SKIN = ROOT / "skin.asterhome"
XML = SERIES / "resources/skins/Default/1080i/SeriesPreview.xml"
MANIFEST = SERIES / "manifest.json"
WRAPPER = SKIN / "tools/aster_v2_series.py"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-series-finish-r15-20261030")

EXPECTED = {
    XML: "33b9a50b9d432adc06f2e8610df74cf66a755201c5339b2866f22997d477a218",
    MANIFEST: "fea1d60a2ba4483597ce5bf0607397a1296d1c031351a1d7008c7b05ce34bb60",
    WRAPPER: "0b637305e6df8809d1c637e6e022a9d4dcfb215d5fe317d7a9e238605d05b726",
    FAMILY: "f4b1cb2ac50c289354567da36864ad8850e2d16b0f7fbce008bdd01068d8e743",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def replace(data: bytes, old: str, new: str, count: int, label: str) -> bytes:
    text = data.decode()
    if text.count(old) != count:
        raise RuntimeError(f"replacement count for {label}: {text.count(old)}")
    return text.replace(old, new).encode()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r15-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def candidates(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    xml = originals[XML]
    xml = replace(xml,
        '<align>center</align><onup>202</onup><ondown>202</ondown><onright>300</onright>',
        '<align>center</align><aligny>center</aligny><onup>202</onup><ondown>202</ondown><onright>300</onright>',
        1, "episode action vertical alignment")
    xml = replace(xml,
        '<align>center</align><onup>200</onup><ondown>202</ondown><onright>300</onright>',
        '<align>center</align><aligny>center</aligny><onup>200</onup><ondown>202</ondown><onright>300</onright>',
        1, "back vertical alignment")
    xml = replace(xml,
        '<texturenofocus border="20" colordiffuse="99000000">special://home/addons/skin.asterhome/media/ui-panel.png</texturenofocus>',
        '<texturenofocus border="20" colordiffuse="cc202b25">special://home/addons/skin.asterhome/media/ui-panel.png</texturenofocus>',
        3, "shared compact control surface")
    xml = replace(xml,
        '<control type="image"><left>12</left><top>40</top><width>198</width><height>118</height><texture diffuse="special://home/addons/skin.asterhome/media/ui-compact-card-mask.png">$INFO[ListItem.Property(Still)]</texture><aspectratio scalediffuse="false">scale</aspectratio></control>',
        '<control type="image"><left>8</left><top>36</top><width>206</width><height>126</height><texture diffuse="special://home/addons/skin.asterhome/media/ui-compact-card-mask.png">$INFO[ListItem.Property(Still)]</texture><aspectratio scalediffuse="false">scale</aspectratio></control>',
        2, "episode still overscan")

    manifest = json.loads(originals[MANIFEST])
    for row in manifest["files"]:
        if row["path"] == "resources/skins/Default/1080i/SeriesPreview.xml":
            row["sha256"] = sha(xml)
            row["bytes"] = len(xml)
    manifest_data = encoded(manifest)
    wrapper = replace(originals[WRAPPER],
        "MANIFEST_SHA='fea1d60a2ba4483597ce5bf0607397a1296d1c031351a1d7008c7b05ce34bb60'",
        f"MANIFEST_SHA='{sha(manifest_data)}'", 1, "wrapper pin")
    family = json.loads(originals[FAMILY])
    family["components"]["aster-series-preview24"]["manifest_sha256"] = sha(manifest_data)
    family["skin"]["tools/aster_v2_series.py"] = sha(wrapper)
    family_data = encoded(family)
    return {XML: xml, MANIFEST: manifest_data, WRAPPER: wrapper, FAMILY: family_data}


def main() -> None:
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    changed = candidates(originals)
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-series-finish-r15", "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(originals[path])
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(originals[path]), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in changed.items():
            atomic_write(path, candidate)
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, original in originals.items():
            atomic_write(path, original)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in changed.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
