#!/usr/bin/env python3
"""Checkpointed two-room AsterTV v3 TV-details installer."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import xml.etree.ElementTree as ET

ROOT = Path("/storage/.kodi/addons")
HERE = Path(__file__).resolve().parent
SERIES = ROOT / "script.asterruntime/aster-series-preview24"
SKIN = ROOT / "skin.asterhome"
WRAPPER = SKIN / "tools/aster_v2_series.py"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
BASELINE = {
    SERIES / "default.py": "dd75885cd19750ccf876e1fa20bf2192d2cc9896e57a83b4b0b18df2b7298032",
    SERIES / "resources/skins/Default/1080i/SeriesPreview.xml": "096b3ab6c329548a2ada0a958306031020c04a85dd0e5aec5fce618a0034cbdf",
    SERIES / "manifest.json": "d5b3d93ecde14574f4a391211fe22a5a7c3a4d3d119332138ef2ed143cab5da9",
    WRAPPER: "0041f06ea9d866e309fc15abf7e4ba59a5c32e2cef56041197f0b2089a967a89",
}
HOSTS = {"AsterTV-Bedroom", "AsterTV-Family"}


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
        raise RuntimeError("active player; deployment refused")


def atomic(path: Path, data: bytes, mode=0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-v3-tv-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def candidates(originals):
    marker = ("\nsys.path.insert(0,str(ROOT))\n"
              "from v3_series_extension import install as _install_v3_series\n"
              "SeriesPreview=_install_v3_series(SeriesPreview)\n\n")
    source = originals[SERIES / "default.py"].decode()
    needle = "\nif __name__=='__main__':main()\n"
    if source.count(needle) != 1:
        raise RuntimeError("series entry marker changed")
    default = source.replace(needle, marker + needle).encode()

    xml = (HERE / "aster-series-preview24/resources/skins/Default/1080i/SeriesPreview.xml").read_bytes()
    ET.fromstring(xml)
    extension = (HERE / "aster-series-preview24/v3_series_extension.py").read_bytes()

    manifest = json.loads(originals[SERIES / "manifest.json"])
    rows = {row["path"]: row for row in manifest["files"]}
    rows["default.py"].update(bytes=len(default), sha256=sha(default))
    rows["resources/skins/Default/1080i/SeriesPreview.xml"].update(bytes=len(xml), sha256=sha(xml))
    rows["v3_series_extension.py"] = {
        "path": "v3_series_extension.py", "bytes": len(extension), "sha256": sha(extension)
    }
    manifest["files"] = [rows[name] for name in sorted(rows)]
    # Keep the stable component kind because the launcher fails closed on it.
    manifest["kind"] = "hp-series-player"
    manifest_data = encoded(manifest)

    wrapper = originals[WRAPPER].decode()
    # The release family manifest and component manifest were reconciled after
    # the wrapper was frozen; this stale pin is the observed native-page
    # regression.  The exact wrapper file hash above makes this repair bounded.
    old_manifest = "c0ebd8db8d2afe49bcde302f2dd5392bed76d4c4a41b8175098b1acc81f399c2"
    if wrapper.count(old_manifest) != 1 or wrapper.count("len(manifest.get('files',[]))!=8") != 1:
        raise RuntimeError("series wrapper guard changed")
    wrapper = wrapper.replace(old_manifest, sha(manifest_data)).replace(
        "len(manifest.get('files',[]))!=8", "len(manifest.get('files',[]))!=9").encode()

    family = json.loads(originals[FAMILY])
    family["components"]["aster-series-preview24"] = {
        "files": 9, "manifest_sha256": sha(manifest_data)
    }
    family["skin"]["tools/aster_v2_series.py"] = sha(wrapper)
    family_data = encoded(family)
    return {
        SERIES / "default.py": default,
        SERIES / "v3_series_extension.py": extension,
        SERIES / "resources/skins/Default/1080i/SeriesPreview.xml": xml,
        SERIES / "manifest.json": manifest_data,
        WRAPPER: wrapper,
        FAMILY: family_data,
        SKIN / "media/ui-button-focus-gold-rim.png": (HERE / "skin.asterhome/media/ui-button-focus-gold-rim.png").read_bytes(),
        SKIN / "media/ui-button-current-gold-rim.png": (HERE / "skin.asterhome/media/ui-button-current-gold-rim.png").read_bytes(),
    }


def main() -> None:
    hostname = socket.gethostname()
    if hostname not in HOSTS:
        raise RuntimeError("unexpected target: " + hostname)
    if Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("recovery marker present")
    active_players()
    originals = {path: path.read_bytes() for path in set(BASELINE) | {FAMILY}}
    for path, expected in BASELINE.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected baseline: " + str(path))
    changed = candidates(originals)
    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    checkpoint = Path("/storage/.aster-checkpoints") / ("astertv-v3-tv-details-" + hostname + "-" + stamp)
    checkpoint.mkdir(parents=True, mode=0o700)
    evidence = {"kind": "astertv-v3-tv-details", "host": hostname, "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        before = path.read_bytes() if path.exists() else None
        if before is not None:
            saved = checkpoint / relative.replace("/", "__")
            saved.write_bytes(before)
            saved.chmod(0o600)
        evidence["files"][relative] = {
            "before": sha(before) if before is not None else None,
            "after": sha(candidate),
        }
    plugin = HERE / "plugin.video.astersearch"
    plugin_target = ROOT / "plugin.video.astersearch"
    if plugin_target.exists():
        raise RuntimeError("actor search target unexpectedly exists")
    evidence["plugin"] = {str(p.relative_to(plugin)): sha(p.read_bytes())
                          for p in sorted(plugin.rglob("*")) if p.is_file()}
    (checkpoint / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")

    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    installed_plugin = False
    try:
        for path, candidate in changed.items():
            atomic(path, candidate)
        shutil.copytree(plugin, plugin_target)
        installed_plugin = True
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
        ET.parse(SERIES / "resources/skins/Default/1080i/SeriesPreview.xml")
    except Exception:
        for path, original in originals.items():
            atomic(path, original)
        for path in changed:
            if path not in originals and path.exists():
                path.unlink()
        if installed_plugin:
            shutil.rmtree(plugin_target, ignore_errors=True)
        Path("/storage/.aster-recovery-required").write_text(str(checkpoint) + "\n")
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "host": hostname, "checkpoint": str(checkpoint),
                      "manifest_sha256": sha(changed[SERIES / "manifest.json"])}, sort_keys=True))


if __name__ == "__main__":
    main()
