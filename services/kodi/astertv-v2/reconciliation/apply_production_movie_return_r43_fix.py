#!/usr/bin/env python3
"""Restore movie details after playback and Search after leaving its child page."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


RUNTIME = Path("/storage/.kodi/addons/script.asterruntime")
SEARCH = RUNTIME / "aster-global-search-ui22"
MOVIE = SEARCH / "movie.py"
MANIFEST = SEARCH / "manifest.json"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-movie-return-r43-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED = {
    MOVIE: "f5e53147fa35d24934b7af3acd02d090e3b5ed3086e21f48fd5fcfb1ff962f1d",
    MANIFEST: "21c0bb13fac1eee843cb7aff0bf348185b2e01ecec6f10efeeb1292da674a66c",
    FAMILY: "9b51492b4b52937beb30e4b88638a5bb8056df79e60ab3b2a5037228705bf3e5",
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return digest(path.read_bytes())


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        raw = b""
        while True:
            raw += client.recv(65536)
            try:
                reply = json.loads(raw)
                break
            except json.JSONDecodeError:
                continue
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def encode(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def patched(movie: bytes, manifest: bytes, family: bytes):
    text = movie.decode()
    entry_old = """        admitted=True
        require(len(sys.argv)==2 and sys.argv[1].isdecimal(),'invalid-movie-link')
        require(not (DIRECTORY/'unresolved-start.json').exists(),'movie-recovery-required')
        require(admitted_source(int(sys.argv[1])) and idle(rpc),'idle-movie-source-required')
"""
    entry_new = """        admitted=True
        source_window=xbmcgui.getCurrentWindowId()
        require(len(sys.argv)==2 and sys.argv[1].isdecimal(),'invalid-movie-link')
        require(not (DIRECTORY/'unresolved-start.json').exists(),'movie-recovery-required')
        require(admitted_source(int(sys.argv[1])) and idle(rpc),'idle-movie-source-required')
"""
    ended_old = """            if ended:
                return_until=time.monotonic()+2
                try:value=read_movie(rpc,value.movie_id);render()
                except MovieUnavailable:window.setProperty('Movie.Status','Progress is syncing. Reopen later to refresh it.')
"""
    ended_new = """            if ended:
                return_until=time.monotonic()+2
                if current!=11130:
                    xbmc.executebuiltin('ActivateWindow(1130)')
                    until=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11130:
                        require(time.monotonic()<until and not monitor.waitForAbort(.05),'movie-return-not-ready')
                    current=11130;xbmc.sleep(300)
                try:value=read_movie(rpc,value.movie_id);render()
                except MovieUnavailable:window.setProperty('Movie.Status','Progress is syncing. Reopen later to refresh it.')
                xbmc.executebuiltin('SetFocus('+('201' if value.has_resume else '200')+')')
"""
    leave_old = """            if session.phase=='idle' and current!=11130 and time.monotonic()>=return_until:break
"""
    leave_new = """            if session.phase=='idle' and current!=11130 and time.monotonic()>=return_until:
                if source_window==11127 and current!=11127:
                    xbmc.executebuiltin('ActivateWindow(1127)')
                    until=time.monotonic()+5
                    while xbmcgui.getCurrentWindowId()!=11127:
                        require(time.monotonic()<until and not monitor.waitForAbort(.05),'search-return-not-ready')
                break
"""
    for old in (entry_old, ended_old, leave_old):
        if text.count(old) != 1:
            raise RuntimeError("unexpected movie return predecessor")
    text = text.replace(entry_old, entry_new, 1)
    text = text.replace(ended_old, ended_new, 1)
    text = text.replace(leave_old, leave_new, 1)
    new_movie = text.encode()
    compile(new_movie, str(MOVIE), "exec")

    component = json.loads(manifest)
    row = next((item for item in component.get("files", [])
                if item.get("path") == "movie.py"), None)
    if row is None or row.get("sha256") != digest(movie):
        raise RuntimeError("Search movie manifest predecessor mismatch")
    row["bytes"] = len(new_movie)
    row["sha256"] = digest(new_movie)
    new_manifest = encode(component)

    accepted = json.loads(family)
    component_row = accepted.get("components", {}).get(
        "aster-global-search-ui22", {})
    if component_row.get("manifest_sha256") != digest(manifest):
        raise RuntimeError("family manifest predecessor mismatch")
    component_row["manifest_sha256"] = digest(new_manifest)
    return new_movie, new_manifest, encode(accepted)


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r43-", dir=path.parent)
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


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise RuntimeError("unexpected predecessor: " + str(path))

    before = {path: path.read_bytes() for path in EXPECTED}
    updated = patched(before[MOVIE], before[MANIFEST], before[FAMILY])
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path in EXPECTED:
        shutil.copy2(path, CHECKPOINT / (path.name + ".before"))
    try:
        for path, data, mode in zip(
                (MOVIE, MANIFEST, FAMILY), updated, (0o755, 0o644, 0o644)):
            atomic_write(path, data, mode)
        component = json.loads(MANIFEST.read_text())
        accepted = json.loads(FAMILY.read_text())
        row = next(item for item in component["files"] if item["path"] == "movie.py")
        if row["sha256"] != sha(MOVIE):
            raise RuntimeError("installed movie manifest mismatch")
        if (accepted["components"]["aster-global-search-ui22"]
                ["manifest_sha256"] != sha(MANIFEST)):
            raise RuntimeError("installed family manifest mismatch")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        for path in (MOVIE, MANIFEST, FAMILY):
            atomic_write(path, before[path], 0o755 if path == MOVIE else 0o644)
        RECOVERY.write_text("r43 movie-return rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "movie_sha256": sha(MOVIE),
        "manifest_sha256": sha(MANIFEST),
        "family_manifest_sha256": sha(FAMILY),
        "integrity_chain_matches": True,
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
