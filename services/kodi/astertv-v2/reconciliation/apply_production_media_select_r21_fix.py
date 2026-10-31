#!/usr/bin/env python3
"""Restore Home media-art details routing on the production v2 client."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


ROOT = Path("/storage/.kodi/addons")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-media-select-r21-20261030")
DISPATCH = ROOT / "skin.asterhome/tools/select_dispatch.py"
SERIES = ROOT / "skin.asterhome/tools/aster_v2_series.py"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
PAYLOAD = Path("/storage/.aster-staging/astertv-r21-media-select")
EXPECTED = {
    DISPATCH: "6f98a11aacb9aeb1493bedb7227e5a46a8328be2c901ae2b15f9dafc10f87520",
    SERIES: "14dd67232b8efe8507ab56fb5151aa0382eee67d685e7df89272da270fd5c3f1",
    FAMILY: "35dd0e7f907a6a18b7f96da98eef55ae8359642720040c25318dfe143d4d297f",
}
REPLACEMENTS = {
    DISPATCH: (PAYLOAD / "select_dispatch.py", "fecf29c1d90fedb95535aa281c2f27317aa3309aebebcc236569a95f43061034"),
    SERIES: (PAYLOAD / "aster_v2_series.py", "31497615fce97c02d7805770c432c8e0ebc3eeeaf35d220996430e45e729d184"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r21-", dir=path.parent)
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
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    for source, expected in REPLACEMENTS.values():
        if sha(source) != expected:
            raise RuntimeError("unexpected payload hash: " + str(source))

    CHECKPOINT.mkdir(parents=True)
    for path in EXPECTED:
        target = CHECKPOINT / path.name
        if target.exists():
            raise RuntimeError("checkpoint collision: " + str(target))
        shutil.copy2(path, target)

    family = json.loads(FAMILY.read_text())
    skin = family.get("skin")
    if not isinstance(skin, dict):
        raise RuntimeError("invalid family manifest")
    skin["tools/select_dispatch.py"] = REPLACEMENTS[DISPATCH][1]
    skin["tools/aster_v2_series.py"] = REPLACEMENTS[SERIES][1]
    family_data = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()

    try:
        for target, (source, _) in REPLACEMENTS.items():
            atomic_write(target, source.read_bytes())
        atomic_write(FAMILY, family_data)
        for target, (_, expected) in REPLACEMENTS.items():
            if sha(target) != expected:
                raise RuntimeError("installed hash mismatch: " + str(target))
    except Exception:
        for path in EXPECTED:
            atomic_write(path, (CHECKPOINT / path.name).read_bytes())
        Path("/storage/.aster-recovery-required").write_text("r21 media-select rollback required\n")
        raise

    (CHECKPOINT / "result.json").write_text(json.dumps({
        "dispatch_sha256": sha(DISPATCH),
        "series_sha256": sha(SERIES),
        "family_sha256": sha(FAMILY),
        "active_players": rpc("Player.GetActivePlayers"),
    }, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
