#!/usr/bin/env python3
"""Route G20 OK directly to Aster's Media and shared Search actions."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


DISPATCH = Path("/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py")
SOURCE = Path(__file__).resolve().parent / "payload/skin.asterhome/tools/select_dispatch.py"
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-search-dispatch-r40-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED = "bd82bb978b54ee73a866bc7152a8ff0747365794650cc5a6a8ae44ac6d65b387"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r40-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o755)
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
    if sha(DISPATCH) != EXPECTED:
        raise RuntimeError("unexpected dispatcher predecessor")
    updated = SOURCE.read_bytes()
    compile(updated, str(SOURCE), "exec")
    text = updated.decode()
    for required in ("window_id == 10000 and focus_id == 135",
                     "focus_id == 139", "aster-global-search-ui22",
                     "header_search.py"):
        if required not in text:
            raise RuntimeError("missing direct Search route: " + required)

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(DISPATCH, CHECKPOINT / "select_dispatch.py.before")
    try:
        atomic_write(DISPATCH, updated)
        if sha(DISPATCH) != hashlib.sha256(updated).hexdigest():
            raise RuntimeError("installed dispatcher hash mismatch")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        atomic_write(DISPATCH, (CHECKPOINT / "select_dispatch.py.before").read_bytes())
        RECOVERY.write_text("r40 Search-dispatch rollback required\n")
        raise

    result = {"installed": True, "checkpoint": str(CHECKPOINT),
              "dispatcher_sha256": sha(DISPATCH),
              "active_players": rpc("Player.GetActivePlayers")}
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
