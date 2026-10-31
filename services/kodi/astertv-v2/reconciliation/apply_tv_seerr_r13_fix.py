#!/usr/bin/env python3
"""Repair the Kodi 22 TV WindowXML identity race and Seerr season layout.

This is a lab-only, hash-guarded overlay.  It refuses active playback,
checkpoints every replaced member, re-pins the component/family manifests,
and restarts Kodi only for the atomic installation window.
"""

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
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-tv-seerr-r13-20261030")

EXPECTED = {
    SERIES / "default.py": "5482c676381cfe253a7aa8dfd211e09e923cef27ebca42dcd52964907187e41d",
    SERIES / "resources/skins/Default/1080i/SeriesPreview.xml": "1b3afc78917339229208c4aea912d6d01a4261a9f8a30963cf509317a6a18d68",
    SERIES / "manifest.json": "11dd14d523015ca1974861e9ec730f969656f21ce411e420fb202044246c78fd",
    SKIN / "tools/aster_v2_series.py": "14d1fb6d793cbe886350118bf9235e2edd179e9fe39050851416a5f020734f3c",
    SKIN / "1080i/custom_1132_requests.xml": "c769cd54c0061816052093c2ad40c8a2a3379e713b33d1b5c1cf75df45b67c7f",
    RUNTIME / "family-manifest.json": "e5590bbe6e62f6d0a3e959103d6fe9575b2abdc5cb95983058eb2c451151051f",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def replace_once(data: bytes, old: str, new: str, label: str) -> bytes:
    text = data.decode()
    if text.count(old) != 1:
        raise RuntimeError(f"replacement count for {label}: {text.count(old)}")
    return text.replace(old, new, 1).encode()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r13-", dir=path.parent)
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
    default_path = SERIES / "default.py"
    default = replace_once(
        originals[default_path],
        """        previous=xbmcgui.Window(source).getFocusId()
        window.show();monitor=xbmc.Monitor();deadline=time.monotonic()+15
        while not monitor.abortRequested() and not window.finished:
""",
        """        previous=xbmcgui.Window(source).getFocusId()
        window.show();monitor=xbmc.Monitor();deadline=time.monotonic()+15
        # Kodi 22 invokes onInit while getCurrentWindowId() can still report
        # the source window.  Publishing that provisional ID makes the owner
        # believe the preview disappeared, leaving an inert orphan page.
        # Wait for the allocated WindowXML ID, publish it, and focus the
        # episode list only after Kodi has committed the transition.
        while not monitor.abortRequested():
            current=xbmcgui.getCurrentWindowId()
            if window.ready and current not in (0,10000,source):break
            if time.monotonic()>deadline:raise SeriesUnavailable('preview-window-identity-timeout')
            if monitor.waitForAbort(.05):break
        if monitor.abortRequested():raise SeriesUnavailable('preview-window-aborted')
        window.identity=current
        home.setProperty('AsterSeries.PreviewWindow',str(current))
        window.setFocusId(300 if window.selection.group else 202)
        while not monitor.abortRequested() and not window.finished:
""",
        "series window identity",
    )
    default = replace_once(
        default,
        """    def populate(self):
        self.setProperty('Series.Ready','false')
        group=self.selection.group
""",
        """    def populate(self):
        self.setProperty('Series.Ready','false')
        group=self.selection.group
        # Season identity belongs to the changing selection, not only to
        # onInit.  Publish it on every cross-season list rebuild.
        self.setProperty('Series.Season',group.label if group else 'No episodes')
        self.setProperty('Series.SeasonIndex',str(self.selection.season))
""",
        "series selected season state",
    )
    default = replace_once(
        default,
        """        self.populate()
        self.setFocusId(300 if self.selection.group else 202)
        # On return Kodi invokes onInit before changing current-window metadata.
""",
        """        self.populate()
        # Initial focus is applied by run_entry only after Kodi publishes the
        # allocated WindowXML ID.  On playback return the stable ID is known.
        if self.identity is not None:self.setFocusId(300 if self.selection.group else 202)
        # On return Kodi invokes onInit before changing current-window metadata.
""",
        "series initial focus timing",
    )

    series_xml_path = SERIES / "resources/skins/Default/1080i/SeriesPreview.xml"
    series_xml = replace_once(
        originals[series_xml_path],
        '<texturefocus/><texturenofocus/><align>left</align><onleft>200</onleft><onright>300</onright><ondown>300</ondown><onup>202</onup><visible>String.IsEqual(Window.Property(Series.Multiple),true)</visible></control>',
        '<texturefocus border="20" colordiffuse="ff005c46">special://home/addons/skin.asterhome/media/ui-panel.png</texturefocus><texturenofocus border="20" colordiffuse="99000000">special://home/addons/skin.asterhome/media/ui-panel.png</texturenofocus><align>center</align><aligny>center</aligny><onleft>200</onleft><onright>300</onright><ondown>300</ondown><onup>202</onup><visible>String.IsEqual(Window.Property(Series.Multiple),true)</visible></control>',
        "series season focus pill",
    )

    manifest_path = SERIES / "manifest.json"
    manifest = json.loads(originals[manifest_path])
    changed = {
        "default.py": default,
        "resources/skins/Default/1080i/SeriesPreview.xml": series_xml,
    }
    for row in manifest["files"]:
        member = changed.get(row["path"])
        if member is not None:
            row["sha256"] = sha(member)
            row["bytes"] = len(member)
    component_manifest = encoded(manifest)

    wrapper_path = SKIN / "tools/aster_v2_series.py"
    wrapper = replace_once(
        originals[wrapper_path],
        "MANIFEST_SHA='1f1142545750c8bde616b698a7ea663006e818b31be9c75c67c589bc36d9d0db'",
        f"MANIFEST_SHA='{sha(component_manifest)}'",
        "series wrapper manifest pin",
    )

    requests_path = SKIN / "1080i/custom_1132_requests.xml"
    requests = originals[requests_path]
    replacements = [
        ('<control type="list" id="40"><left>1210</left><top>190</top><width>570</width><height>360</height>',
         '<control type="list" id="40"><left>1210</left><top>190</top><width>570</width><height>300</height>'),
        ('<control type="button" id="41"><left>1210</left><top>560</top><width>570</width><height>52</height><label>Select season</label>',
         '<control type="button" id="41"><left>1210</left><top>505</top><width>570</width><height>56</height><label>Select season</label>'),
        ('<font>font20</font><textcolor>asterIvory</textcolor><focusedcolor>asterIvory</focusedcolor><texturefocus border="18" colordiffuse="asterGreen">special://skin/media/ui-panel.png</texturefocus>',
         '<font>font20</font><textcolor>asterIvory</textcolor><focusedcolor>asterIvory</focusedcolor><align>center</align><aligny>center</aligny><texturefocus border="18" colordiffuse="asterGreen">special://skin/media/ui-panel.png</texturefocus>'),
        ('<control type="label"><left>1210</left><top>618</top><width>570</width><height>40</height>',
         '<control type="label"><left>1210</left><top>568</top><width>570</width><height>36</height>'),
        ('<control type="button" id="50"><left>1210</left><top>675</top><width>570</width><height>64</height><label>',
         '<control type="button" id="50"><left>1210</left><top>615</top><width>570</width><height>64</height><label>'),
        ('<font>font24</font><textcolor>asterIvory</textcolor><focusedcolor>asterIvory</focusedcolor><texturefocus border="20" colordiffuse="asterGreen">special://skin/media/ui-panel.png</texturefocus>',
         '<font>font24</font><textcolor>asterIvory</textcolor><focusedcolor>asterIvory</focusedcolor><align>center</align><aligny>center</aligny><texturefocus border="20" colordiffuse="asterGreen">special://skin/media/ui-panel.png</texturefocus>'),
    ]
    for index, (old, new) in enumerate(replacements):
        requests = replace_once(requests, old, new, f"Seerr layout {index}")

    family_path = RUNTIME / "family-manifest.json"
    family = json.loads(originals[family_path])
    family["components"]["aster-series-preview24"]["manifest_sha256"] = sha(component_manifest)
    family["skin"]["tools/aster_v2_series.py"] = sha(wrapper)
    family["skin"]["1080i/custom_1132_requests.xml"] = sha(requests)
    family_manifest = encoded(family)

    return {
        default_path: default,
        series_xml_path: series_xml,
        manifest_path: component_manifest,
        wrapper_path: wrapper,
        requests_path: requests,
        family_path: family_manifest,
    }


def main() -> None:
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    originals = {}
    for path, expected in EXPECTED.items():
        data = path.read_bytes()
        if sha(data) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
        originals[path] = data
    changed = candidates(originals)
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-tv-seerr-r13", "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(originals[path])
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(originals[path]), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    (CHECKPOINT / "manifest.json").chmod(0o600)
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in changed.items():
            atomic_write(path, candidate)
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path in changed:
            atomic_write(path, originals[path])
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in changed.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
