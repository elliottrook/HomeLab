#!/usr/bin/env python3
"""Connect the v3 TV synopsis, season, trailer, and actor controls."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path("/storage/.kodi/addons")
HERE = Path(__file__).resolve().parent
SERIES = ROOT / "script.asterruntime/aster-series-preview24"
XML = SERIES / "resources/skins/Default/1080i/SeriesPreview.xml"
EXTENSION = SERIES / "v3_series_extension.py"
MANIFEST = SERIES / "manifest.json"
WRAPPER = ROOT / "skin.asterhome/tools/aster_v2_series.py"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
TRAILER_ICON = ROOT / "skin.asterhome/media/player-controls/trailer.png"
EXPECTED = {
    XML: "a0d3a2764c5d1f661ea273a880ff794698466d844ab1bc0814950b397802df7c",
    EXTENSION: "4e94f92818f4bf3ab4b48677426bffa6cc83c7e94c5ef9854ec2d087404903ef",
    MANIFEST: "6256883cc10d92f343305e437cbfb199ce60af6a801507664528d387b6e21126",
    WRAPPER: "f1791235e6223731106ca781269b407cab4568732f4a0ce0c0231d28812de521",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player; repair refused")


def enable_actor_search() -> None:
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "Addons.SetAddonEnabled",
        "params": {"addonid": "plugin.video.astersearch", "enabled": True},
    }
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", 9090), timeout=1) as client:
                client.settimeout(3)
                client.sendall((json.dumps(request) + "\n").encode())
                if json.loads(client.recv(4096).decode()).get("result") == "OK":
                    return
        except (OSError, ValueError, json.JSONDecodeError):
            time.sleep(0.5)
    raise RuntimeError("actor search could not be enabled")


def atomic(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-v3-connections-", dir=path.parent)
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


def main() -> None:
    hostname = socket.gethostname()
    if hostname not in ("AsterTV-Bedroom", "AsterTV-Family"):
        raise RuntimeError("unexpected target: " + hostname)
    if Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("recovery marker present")
    active_players()

    originals = {path: path.read_bytes() for path in set(EXPECTED) | {FAMILY}}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("baseline drift: " + str(path))

    xml = (HERE / "aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml").read_bytes()
    extension = (HERE / "aster-series-preview24/v3_series_extension.py").read_bytes()
    ET.fromstring(xml)
    for marker in (b"ListItem.Property(Still)", b"ListItem.Property(Synopsis)",
                   b"ListItem.Property(Metadata)", b"player-controls/trailer.png"):
        if marker not in xml:
            raise RuntimeError("missing XML repair marker: " + marker.decode())
    for marker in (b"group.number not in (None, 0)", b"self._v3_season_indices",
                   b"AlarmClock(AsterActor,"):
        if marker not in extension:
            raise RuntimeError("missing controller repair marker: " + marker.decode())

    manifest = json.loads(originals[MANIFEST])
    rows = {row["path"]: row for row in manifest["files"]}
    rows["resources/skins/Default/1080i/SeriesPreview.xml"].update(
        bytes=len(xml), sha256=sha(xml))
    rows["v3_series_extension.py"].update(bytes=len(extension), sha256=sha(extension))
    manifest["files"] = [rows[name] for name in sorted(rows)]
    manifest_data = encoded(manifest)

    wrapper = originals[WRAPPER].decode()
    if wrapper.count(EXPECTED[MANIFEST]) != 1:
        raise RuntimeError("wrapper manifest pin drift")
    wrapper_data = wrapper.replace(EXPECTED[MANIFEST], sha(manifest_data)).encode()
    family = json.loads(originals[FAMILY])
    family["components"]["aster-series-preview24"] = {
        "files": 9,
        "manifest_sha256": sha(manifest_data),
    }
    family["skin"]["tools/aster_v2_series.py"] = sha(wrapper_data)
    family_data = encoded(family)
    changed = {
        XML: xml,
        EXTENSION: extension,
        MANIFEST: manifest_data,
        WRAPPER: wrapper_data,
        FAMILY: family_data,
        TRAILER_ICON: (HERE / "skin.asterhome/media/player-controls/trailer.png").read_bytes(),
    }

    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    checkpoint = Path("/storage/.aster-checkpoints") / (
        "astertv-v3-tv-connections-" + hostname + "-" + stamp)
    checkpoint.mkdir(mode=0o700)
    for path in changed:
        saved = checkpoint / str(path.relative_to(ROOT)).replace("/", "__")
        if path in originals:
            saved.write_bytes(originals[path])
            saved.chmod(0o600)

    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, data in changed.items():
            atomic(path, data)
        for path, data in changed.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError("post-write mismatch: " + str(path))
        ET.parse(XML)
    except Exception:
        for path, data in originals.items():
            atomic(path, data)
        if TRAILER_ICON not in originals and TRAILER_ICON.exists():
            TRAILER_ICON.unlink()
        Path("/storage/.aster-recovery-required").write_text(str(checkpoint) + "\n")
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)

    try:
        enable_actor_search()
    except Exception:
        Path("/storage/.aster-recovery-required").write_text(str(checkpoint) + "\n")
        raise

    print(json.dumps({
        "installed": True,
        "host": hostname,
        "checkpoint": str(checkpoint),
        "manifest_sha256": sha(manifest_data),
        "xml_sha256": sha(xml),
        "extension_sha256": sha(extension),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
