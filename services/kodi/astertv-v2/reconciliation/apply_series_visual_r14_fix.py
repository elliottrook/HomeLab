#!/usr/bin/env python3
"""Apply the compact Series controls, clock pill and canonical watch badges."""
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
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-series-visual-r14-20261030")

EXPECTED = {
    XML: "801c3f66dd5caa46db3af1dbd97d08b38c662bec998da28bc9f155fe713bae04",
    MANIFEST: "8ddc7f8949438e33aebc2821fe2a2fcdebe185573878c4f8dececcb068c382a9",
    WRAPPER: "0d6142f6da2687a11717cad4034221486246d4085e53c9d059184f4b7cfa6fab",
    FAMILY: "83e8c11bb040f6cf051b493f9ad12f23a0d49ab0729fdbd9b2f5b46317305b64",
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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r14-", dir=path.parent)
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
    old_clock = """<control type="image"><left>1714</left><top>30</top><width>147</width><height>50</height><texture border="20" colordiffuse="ffad8a4d">special://home/addons/skin.asterhome/media/ui-panel.png</texture></control>
<control type="image"><left>1715</left><top>31</top><width>145</width><height>48</height><texture border="20" colordiffuse="fff3eee5">special://home/addons/skin.asterhome/media/ui-panel.png</texture></control>
<control type="label"><left>1715</left><top>31</top><width>145</width><height>48</height><label>$INFO[System.Time(hh:mm)]</label><font>font24</font><textcolor>fff3eee5</textcolor><align>center</align><aligny>center</aligny></control>"""
    new_clock = """<control type="image"><left>1714</left><top>30</top><width>146</width><height>44</height><texture border="20" colordiffuse="75cbb991">special://home/addons/skin.asterhome/media/ui-panel.png</texture></control>
<control type="image"><left>1716</left><top>32</top><width>142</width><height>40</height><texture border="20" colordiffuse="f23b3a32">special://home/addons/skin.asterhome/media/ui-panel.png</texture></control>
<control type="label"><left>1714</left><top>30</top><width>146</width><height>44</height><label>$INFO[System.Time(HH:mm)]</label><font>font20</font><textcolor>fff3eee5</textcolor><align>center</align><aligny>center</aligny></control>"""
    xml = replace(xml, old_clock, new_clock, 1, "clock pill")
    xml = replace(xml,
        '<control type="button" id="200"><left>125</left><top>755</top><width>680</width><height>64</height><label>$INFO[Window.Property(Series.Primary)]</label><font>font24</font>',
        '<control type="button" id="200"><left>125</left><top>755</top><width>240</width><height>46</height><label>$INFO[Window.Property(Series.Primary)]</label><font>font20</font>',
        1, "episode action geometry")
    xml = replace(xml,
        '<control type="button" id="202"><left>125</left><top>855</top><width>240</width><height>64</height><label>‹ Back</label><font>font24</font>',
        '<control type="button" id="202"><left>125</left><top>820</top><width>140</width><height>46</height><label>‹ Back</label><font>font20</font>',
        1, "back geometry")
    xml = replace(xml,
        '<control type="button" id="201"><left>905</left><top>200</top><width>880</width><height>54</height><label>$INFO[Window.Property(Series.Season)]  ▾</label><font>font28</font>',
        '<control type="button" id="201"><left>905</left><top>204</top><width>220</width><height>46</height><label>$INFO[Window.Property(Series.Season)]  ▾</label><font>font20</font>',
        1, "season geometry")
    xml = replace(xml,
        '<control type="label"><left>905</left><top>200</top><width>880</width><height>54</height><label>$INFO[Window.Property(Series.Season)]</label><font>font28</font>',
        '<control type="label"><left>905</left><top>204</top><width>220</width><height>46</height><label>$INFO[Window.Property(Series.Season)]</label><font>font20</font>',
        1, "single season geometry")
    old_badge = '<control type="label"><left>174</left><top>42</top><width>30</width><height>30</height><label>●</label><font>font24</font><textcolor>ff00a878</textcolor><align>center</align><visible>String.IsEqual(ListItem.Property(Watched),true)</visible></control>'
    new_badge = ('<control type="label"><left>174</left><top>42</top><width>32</width><height>32</height><label>●</label><font>font16</font><textcolor>ff91c6a2</textcolor><align>center</align><aligny>center</aligny><visible>!String.IsEqual(ListItem.Property(Watched),true)</visible></control>'
        '<control type="image"><left>174</left><top>42</top><width>32</width><height>32</height><texture colordiffuse="ff91c6a2">special://home/addons/skin.asterhome/media/ui-timer-dot.png</texture><visible>String.IsEqual(ListItem.Property(Watched),true)</visible></control>'
        '<control type="label"><left>174</left><top>42</top><width>32</width><height>32</height><label>✓</label><font>font16</font><textcolor>ff3b3a32</textcolor><align>center</align><aligny>center</aligny><visible>String.IsEqual(ListItem.Property(Watched),true)</visible></control>')
    xml = replace(xml, old_badge, new_badge, 2, "episode watch badge")
    xml = replace(xml,
        '<texture>$INFO[ListItem.Property(Still)]</texture><aspectratio>scale</aspectratio>',
        '<texture diffuse="special://home/addons/skin.asterhome/media/ui-compact-card-mask.png">$INFO[ListItem.Property(Still)]</texture><aspectratio scalediffuse="false">scale</aspectratio>',
        2, "rounded episode still")

    manifest = json.loads(originals[MANIFEST])
    for row in manifest["files"]:
        if row["path"] == "resources/skins/Default/1080i/SeriesPreview.xml":
            row["sha256"] = sha(xml)
            row["bytes"] = len(xml)
    manifest_data = encoded(manifest)
    wrapper = replace(originals[WRAPPER],
        "MANIFEST_SHA='8ddc7f8949438e33aebc2821fe2a2fcdebe185573878c4f8dececcb068c382a9'",
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
    evidence = {"kind": "astertv-v2-series-visual-r14", "files": {}}
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
