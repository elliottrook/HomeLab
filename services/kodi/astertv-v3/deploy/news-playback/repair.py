#!/usr/bin/env python3
"""Repair News playback after Kodi retains an inactive media playlist.

The repair is host-bound, exact-baseline pinned, checkpointed and atomic.  It
changes the digest player's readiness rule from "no player and no remembered
playlist items" to "no active player", while snapshotting both playlists and
failing playback ownership if the direct digest player changes either queue.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ADDONS = Path("/storage/.kodi/addons")
PLAYER = ADDONS / "script.asterruntime/aster-digest-player8"
PORT = PLAYER / "resources/lib/digest_kodi_port.py"
MANIFEST = PLAYER / "manifest.json"
FAMILY = ADDONS / "script.asterruntime/family-manifest.json"
WRAPPER = ADDONS / "skin.asterhome/tools/aster_v2_digest.py"
GUARD = Path("/storage/.aster-release/release_guard.py")
MARKER = Path("/storage/.aster-release/news-playback-repair.json")
BASELINES = {
    PORT: "780f6c014d97fac80aa7fb37b5a8c4309ecb84d4261d0f8888e0f8ab235ebc0d",
    MANIFEST: "9e3644b7d012bc7610f7366608456ce06ffe1d8b6eee315574bb762d5a186e9c",
    FAMILY: "9804e0debba103dc084b79280e9088d1c00b0dfbdccb696c53a997f8457a9689",
    WRAPPER: "a06cfc95840d218d637671a025b147336cdf17318d0c1ac991d5eaf404e6ed25",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_port(source: str) -> str:
    old_idle = """def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(playlistid=i,
        limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))
"""
    new_idle = """def queue_state():
    snapshots = []
    for playlist_id in (0, 1):
        result = rpc('Playlist.GetItems', dict(playlistid=playlist_id,
            properties=['file'], limits=dict(start=0, end=1000)))
        total = result['limits']['total']
        if total > 1000 or len(result['items']) != total:
            raise ValueError('bounded-playlist-snapshot-required')
        snapshots.append((total, tuple(item.get('file', '') for item in result['items'])))
    return tuple(snapshots)


def idle():
    # Kodi normally retains the last played item in a playlist after playback
    # stops. Readiness means no active player; queue preservation is enforced
    # independently by KodiPort.queue_snapshot.
    return not rpc('Player.GetActivePlayers')
"""
    old_init = "        self.last_target = 0\n"
    new_init = old_init + "        self.queue_snapshot = None\n"
    old_open = """    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.opened = True
        self.player.play(str(self.path))
"""
    new_open = """    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.queue_snapshot = queue_state()
        self.opened = True
        self.player.play(str(self.path))
"""
    old_owned = """                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature)
        except (OSError, RuntimeError): return False
"""
    new_owned = """                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature
                and queue_state() == self.queue_snapshot)
        except (OSError, RuntimeError, ValueError): return False
"""
    for old, new, name in (
        (old_idle, new_idle, "idle"),
        (old_init, new_init, "init"),
        (old_open, new_open, "open"),
        (old_owned, new_owned, "owned"),
    ):
        if source.count(old) != 1:
            raise ValueError("port-" + name + "-baseline-drift")
        source = source.replace(old, new)
    return source


def build_payload(port: bytes, manifest: bytes, family: bytes, wrapper: bytes) -> dict[Path, bytes]:
    new_port = patch_port(port.decode()).encode()
    player = json.loads(manifest)
    matches = [row for row in player["files"] if row["path"] == "resources/lib/digest_kodi_port.py"]
    if len(matches) != 1:
        raise ValueError("player-port-member-drift")
    matches[0]["bytes"] = len(new_port)
    matches[0]["sha256"] = sha(new_port)
    new_manifest = (json.dumps(player, indent=2, sort_keys=True) + "\n").encode()
    old_pin = sha(manifest)
    new_pin = sha(new_manifest)
    wrapper_text = wrapper.decode()
    needle = "PIN = '" + old_pin + "'"
    if wrapper_text.count(needle) != 1:
        raise ValueError("wrapper-player-pin-drift")
    new_wrapper = wrapper_text.replace(needle, "PIN = '" + new_pin + "'").encode()
    family_data = json.loads(family)
    component = family_data["components"]["aster-digest-player8"]
    if component["manifest_sha256"] != old_pin:
        raise ValueError("family-player-pin-drift")
    component["manifest_sha256"] = new_pin
    if family_data["skin"]["tools/aster_v2_digest.py"] != sha(wrapper):
        raise ValueError("family-wrapper-pin-drift")
    family_data["skin"]["tools/aster_v2_digest.py"] = sha(new_wrapper)
    new_family = (json.dumps(family_data, indent=2, sort_keys=True) + "\n").encode()
    return {PORT: new_port, MANIFEST: new_manifest, WRAPPER: new_wrapper, FAMILY: new_family}


def atomic(path: Path, data: bytes, mode: int | None = None) -> None:
    fd, temporary = tempfile.mkstemp(prefix=".news-playback-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode if mode is not None else path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def verified_marker() -> bool:
    if not MARKER.is_file():
        return False
    data = json.loads(MARKER.read_text())
    return data.get("host") == "AsterTV-Family" and all(
        path.is_file() and sha(path.read_bytes()) == expected
        for path, expected in ((Path(name), digest) for name, digest in data.get("files", {}).items())
    )


def main() -> None:
    if socket.gethostname() != "AsterTV-Family":
        raise SystemExit("family-target-required")
    if verified_marker():
        print(json.dumps({"host": "AsterTV-Family", "outcome": "already-installed"}, sort_keys=True))
        return
    if subprocess.run(["systemctl", "is-active", "--quiet", "kodi"], check=False).returncode == 0:
        raise SystemExit("kodi-must-be-stopped")
    originals = {path: path.read_bytes() for path in BASELINES}
    for path, expected in BASELINES.items():
        if sha(originals[path]) != expected:
            raise SystemExit("baseline-drift:" + str(path))
    payload = build_payload(originals[PORT], originals[MANIFEST], originals[FAMILY], originals[WRAPPER])
    checkpoint = Path("/storage/.aster-checkpoints") / (
        "astertv-news-playback-AsterTV-Family-" + time.strftime("%Y%m%d-%H%M%S", time.gmtime()))
    checkpoint.mkdir(mode=0o700, parents=True)
    for path, data in originals.items():
        target = checkpoint / path.relative_to(ADDONS)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(data)
    for path, data in payload.items():
        atomic(path, data)
    verify = subprocess.run(
        [sys.executable, str(GUARD), "snapshot", "--host", "AsterTV-Family"],
        check=True, capture_output=True, text=True,
    )
    clean = subprocess.run(
        [sys.executable, str(GUARD), "verify", "--host", "AsterTV-Family"],
        check=True, capture_output=True, text=True,
    )
    report = {
        "host": "AsterTV-Family",
        "outcome": "installed",
        "checkpoint": str(checkpoint),
        "files": {str(path): sha(data) for path, data in payload.items()},
        "accepted": json.loads(verify.stdout),
        "verified": json.loads(clean.stdout),
    }
    atomic(MARKER, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode(), 0o600)
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
