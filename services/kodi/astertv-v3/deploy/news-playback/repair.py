#!/usr/bin/env python3
"""Repair News lifecycle after Kodi retains or self-updates an audio playlist.

The repair is host-bound, exact-baseline pinned, checkpointed and atomic.  It
changes the digest player's readiness rule from "no player and no remembered
playlist items" to "no active player". It permits only Kodi's exact transition
to the player's unique private session file, freezes that resulting snapshot,
and fails playback ownership on every other queue change.
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
    "AsterTV-Family": {
        PORT: "780f6c014d97fac80aa7fb37b5a8c4309ecb84d4261d0f8888e0f8ab235ebc0d",
        MANIFEST: "9e3644b7d012bc7610f7366608456ce06ffe1d8b6eee315574bb762d5a186e9c",
        FAMILY: "9804e0debba103dc084b79280e9088d1c00b0dfbdccb696c53a997f8457a9689",
        WRAPPER: "a06cfc95840d218d637671a025b147336cdf17318d0c1ac991d5eaf404e6ed25",
    },
    # AsterTV-Jen has the same reviewed player member as Family's predecessor,
    # but its six hostname-gated runtime manifests were repinned independently.
    "AsterTV-Jen": {
        PORT: "0c8e23e69259103906c4ea70f165181aa02c7713bf0ae4963c2989219d892134",
        MANIFEST: "f8c82cc197c0ce7d584c82804e619a07b98b0f5aeda6a14f82f18d617d4f5907",
        FAMILY: "888cc7060b7c56108aa240b0987bd55200d98f60e75af63d8620d499d50887ec",
        WRAPPER: "96fbbcd439168eb7785a2587e360a31792dbb4390c6951c846d4465af59bc06b",
    },
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
    new_init = old_init + "        self.queue_before = None\n        self.queue_snapshot = None\n"
    old_open = """    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.opened = True
        self.player.play(str(self.path))
"""
    new_open = """    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.queue_before = queue_state()
        self.queue_snapshot = None
        self.opened = True
        self.player.play(str(self.path))
"""
    queue_check = """    def queue_unchanged(self):
        current = queue_state()
        if self.queue_snapshot is not None:
            return current == self.queue_snapshot
        if self.queue_before is None or current[1] != self.queue_before[1]:
            return False
        own_audio = (1, (str(self.path),))
        if current[0] not in (self.queue_before[0], own_audio):
            return False
        self.queue_snapshot = current
        return True

"""
    old_owned_entry = "    def owned(self):\n"
    new_owned_entry = queue_check + old_owned_entry
    old_owned = """                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature)
        except (OSError, RuntimeError): return False
"""
    new_owned = """                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature
                and self.queue_unchanged())
        except (OSError, RuntimeError, ValueError): return False
"""
    legacy_init = old_init + "        self.queue_snapshot = None\n"
    legacy_open = """    def open(self):
        if self.opened or not idle(): raise ValueError('idle-single-open-required')
        self.queue_snapshot = queue_state()
        self.opened = True
        self.player.play(str(self.path))
"""
    legacy_owned = old_owned.replace(
        "                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature)\n",
        "                and (meta.st_dev, meta.st_ino, meta.st_size, meta.st_mtime_ns) == self.signature\n"
        "                and queue_state() == self.queue_snapshot)\n").replace(
            "except (OSError, RuntimeError):", "except (OSError, RuntimeError, ValueError):")
    if old_idle in source:
        replacements = ((old_idle, new_idle, "idle"), (old_init, new_init, "init"),
                        (old_open, new_open, "open"), (old_owned_entry, new_owned_entry, "queue-check"),
                        (old_owned, new_owned, "owned"))
    elif legacy_init in source and legacy_open in source and legacy_owned in source:
        replacements = ((legacy_init, new_init, "legacy-init"),
                        (legacy_open, new_open, "legacy-open"),
                        (old_owned_entry, new_owned_entry, "legacy-queue-check"),
                        (legacy_owned, new_owned, "legacy-owned"))
    else:
        raise ValueError("port-baseline-drift")
    for old, new, name in replacements:
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


def verified_marker(host: str) -> bool:
    if not MARKER.is_file():
        return False
    data = json.loads(MARKER.read_text())
    revision_ok = host != "AsterTV-Jen" or data.get("revision") == 2
    return data.get("host") == host and revision_ok and all(
        path.is_file() and sha(path.read_bytes()) == expected
        for path, expected in ((Path(name), digest) for name, digest in data.get("files", {}).items())
    )


def main() -> None:
    host = socket.gethostname()
    if host not in BASELINES:
        raise SystemExit("news-repair-target-required")
    if verified_marker(host):
        print(json.dumps({"host": host, "outcome": "already-installed"}, sort_keys=True))
        return
    if subprocess.run(["systemctl", "is-active", "--quiet", "kodi"], check=False).returncode == 0:
        raise SystemExit("kodi-must-be-stopped")
    baselines = BASELINES[host]
    originals = {path: path.read_bytes() for path in baselines}
    for path, expected in baselines.items():
        if sha(originals[path]) != expected:
            raise SystemExit("baseline-drift:" + str(path))
    payload = build_payload(originals[PORT], originals[MANIFEST], originals[FAMILY], originals[WRAPPER])
    checkpoint = Path("/storage/.aster-checkpoints") / (
        "astertv-news-playback-" + host + "-" + time.strftime("%Y%m%d-%H%M%S", time.gmtime()))
    checkpoint.mkdir(mode=0o700, parents=True)
    for path, data in originals.items():
        target = checkpoint / path.relative_to(ADDONS)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        target.write_bytes(data)
    for path, data in payload.items():
        atomic(path, data)
    verify = subprocess.run(
        [sys.executable, str(GUARD), "snapshot", "--host", host],
        check=True, capture_output=True, text=True,
    )
    clean = subprocess.run(
        [sys.executable, str(GUARD), "verify", "--host", host],
        check=True, capture_output=True, text=True,
    )
    report = {
        "revision": 2,
        "host": host,
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
