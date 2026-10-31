#!/usr/bin/env python3
"""Install the pinned AsterTV Kodi splash on lab or production."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

SOURCE = Path(__file__).with_name("Splash.png")
TARGET = Path("/storage/.kodi/media/Splash.png")
EXPECTED_SOURCE = "912228f3866b33749905eb8154b470d3170fe4747f92799811470bb49b986cce"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-splash-", dir=path.parent)
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
    host = os.uname().nodename
    if host not in ("AsterTV", "AsterTVProd"):
        raise RuntimeError("AsterTV host only")
    checkpoint = Path("/storage/.aster-checkpoints/astertv-v2-splash-r18-20261030-" + host)
    if checkpoint.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    candidate = SOURCE.read_bytes()
    if sha(candidate) != EXPECTED_SOURCE:
        raise RuntimeError("unexpected AsterTV splash hash")
    original = TARGET.read_bytes() if TARGET.is_file() else None
    checkpoint.mkdir(mode=0o700, parents=True)
    if original is not None:
        (checkpoint / "Splash.png.before").write_bytes(original)
        (checkpoint / "Splash.png.before").chmod(0o600)
    (checkpoint / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-kodi-splash-r18",
        "host": host,
        "before": sha(original) if original is not None else None,
        "after": sha(candidate),
        "restore": "copy Splash.png.before to target" if original is not None else "remove target",
    }, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=40)
    try:
        atomic_write(TARGET, candidate)
        if sha(TARGET.read_bytes()) != EXPECTED_SOURCE:
            raise RuntimeError("post-write mismatch")
    except Exception:
        if original is not None:
            atomic_write(TARGET, original)
        elif TARGET.exists():
            TARGET.unlink()
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=40)
    print(json.dumps({"installed": True, "host": host, "target": str(TARGET),
                      "sha256": EXPECTED_SOURCE, "checkpoint": str(checkpoint)}, sort_keys=True))


if __name__ == "__main__":
    main()
