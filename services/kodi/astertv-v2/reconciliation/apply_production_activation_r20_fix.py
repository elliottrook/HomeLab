#!/usr/bin/env python3
"""Repair production host fences and Kodi add-on activation without restart."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import tempfile

ROOT = Path("/storage/.kodi/addons")
DATABASES = Path("/storage/.kodi/userdata/Database")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-production-activation-r20-20261030")
MUSIC = ROOT / "script.astermusic.v2lab/default.py"
ACQUISITION = ROOT / "script.asteracquisition/default.py"
SCREENSAVER = ROOT / "screensaver.asterhome.v2lab/default.py"
MUSIC_MANIFEST = ROOT / "script.asterruntime/music72-manifest.json"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
EXPECTED = {
    MUSIC: "3419eb149d2a0a11066050dc420a7cdc049df6866a5371da9f6d214253ffb375",
    ACQUISITION: "0b9d5fcfb55aac34dd5527d5fd9cb37d695da29138e859eb072cdf682bf78714",
    SCREENSAVER: "b7d1f3bd214236f7ce90fa36d866a05fad309eb8b9b0c8ff26f0e3280dfa15c0",
    MUSIC_MANIFEST: "67e2986698cc8f23acedaf410af3aed3d3e4b5dd0a2bac4e09a75618d169afa3",
    FAMILY: "7c308df13b693c0588f2b99af09b5e46aabf3219a928fdc93f141654291c79ff",
}
RUNTIME_ADDONS = (
    "screensaver.asterhome.v2lab",
    "script.asteracquisition",
    "script.astermusic.v2lab",
    "script.asterruntime",
    "script.asterseerr",
    "script.astervoice.v2lab",
    "service.aster.playerui",
    "service.aster.startup",
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def replace_once(data: bytes, old: str, new: str) -> bytes:
    text = data.decode()
    if text.count(old) != 1:
        raise RuntimeError("replacement source count: " + old)
    return text.replace(old, new, 1).encode()


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r20-", dir=path.parent)
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
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))

    music = replace_once(
        originals[MUSIC],
        "if platform.node()!='AsterTV' or (kind!='pilot' and not normal_playback()):",
        "if platform.node() not in ('AsterTV','AsterTVProd') or (kind!='pilot' and not normal_playback()):",
    )
    music = replace_once(
        music,
        "Normal Music integration is enabled only on the HP lab.",
        "Normal Music integration is not enabled on this Aster client.",
    )
    acquisition = replace_once(
        originals[ACQUISITION],
        'if os.uname().nodename != "AsterTV":',
        'if os.uname().nodename not in ("AsterTV", "AsterTVProd"):',
    )
    screensaver = replace_once(
        originals[SCREENSAVER],
        "if os.uname().nodename!='AsterTV' or not active():return",
        "if os.uname().nodename not in ('AsterTV','AsterTVProd') or not active():return",
    )
    for name, data in (("music", music), ("acquisition", acquisition),
                       ("screensaver", screensaver)):
        compile(data, name + ".py", "exec")

    manifest = json.loads(originals[MUSIC_MANIFEST])
    matches = [row for row in manifest["files"]
               if row["path"] == "script.astermusic.v2lab/default.py"]
    if len(matches) != 1:
        raise RuntimeError("music manifest member")
    matches[0]["bytes"] = len(music)
    matches[0]["sha256"] = sha(music)
    music_manifest = encoded(manifest)
    family = json.loads(originals[FAMILY])
    family["music_manifest_sha256"] = sha(music_manifest)
    family_bytes = encoded(family)
    candidates = {
        MUSIC: music,
        ACQUISITION: acquisition,
        SCREENSAVER: screensaver,
        MUSIC_MANIFEST: music_manifest,
        FAMILY: family_bytes,
    }

    database = sorted(DATABASES.glob("Addons*.db"))[-1]
    source = sqlite3.connect(str(database))
    prior = dict(source.execute(
        "select addonID,enabled from installed where addonID like '%aster%'"))
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    backup = CHECKPOINT / database.name
    destination = sqlite3.connect(str(backup))
    source.backup(destination)
    destination.close()
    source.close()
    backup.chmod(0o600)
    for path, data in originals.items():
        saved = CHECKPOINT / (str(path.relative_to(ROOT)).replace("/", "__") + ".before")
        saved.write_bytes(data)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-production-activation-r20",
        "files": {str(path.relative_to(ROOT)): {"before": sha(originals[path]),
                                                   "after": sha(candidates[path])}
                  for path in candidates},
        "enabled_before": prior,
        "enable": RUNTIME_ADDONS,
        "disable": ["script.asterbootstrap"],
    }, indent=2, sort_keys=True) + "\n")
    try:
        for path, data in candidates.items():
            atomic_write(path, data)
        for addon in RUNTIME_ADDONS:
            if rpc("Addons.SetAddonEnabled", {"addonid": addon, "enabled": True}) != "OK":
                raise RuntimeError("enable failed: " + addon)
        if rpc("Addons.SetAddonEnabled", {"addonid": "script.asterbootstrap", "enabled": False}) != "OK":
            raise RuntimeError("bootstrap disable failed")
        for path, data in candidates.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, data in originals.items():
            atomic_write(path, data)
        for addon, enabled in prior.items():
            rpc("Addons.SetAddonEnabled", {"addonid": addon, "enabled": bool(enabled)})
        raise
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in candidates.items()},
                      "enabled": RUNTIME_ADDONS,
                      "disabled": ["script.asterbootstrap"]}, sort_keys=True))


if __name__ == "__main__":
    main()
