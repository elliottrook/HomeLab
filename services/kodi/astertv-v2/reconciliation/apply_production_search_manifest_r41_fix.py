#!/usr/bin/env python3
"""Reconcile Search's accepted dispatcher hash after the guarded r40 update."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


DISPATCH = Path("/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py")
FAMILY = Path("/storage/.kodi/addons/script.asterruntime/family-manifest.json")
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-search-manifest-r41-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED_DISPATCH = "6b60681bc187c168e5b17abee542a9b2c2ab112e79865273d0f00d4de5b7b44e"
EXPECTED_FAMILY = "3eb70fde6084a73ff90353ab2edb8fa55d270c5413f78eecb2573d2fe6358cf3"
OLD_ACCEPTED_DISPATCH = "fecf29c1d90fedb95535aa281c2f27317aa3309aebebcc236569a95f43061034"


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


def encode(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r41-", dir=path.parent)
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


def reconciled_family(data: bytes, dispatch_hash: str) -> bytes:
    family = json.loads(data)
    accepted = family.get("skin", {}).get("tools/select_dispatch.py")
    if accepted != OLD_ACCEPTED_DISPATCH:
        raise RuntimeError("unexpected accepted dispatcher predecessor")
    family["skin"]["tools/select_dispatch.py"] = dispatch_hash
    return encode(family)


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if sha(DISPATCH) != EXPECTED_DISPATCH or sha(FAMILY) != EXPECTED_FAMILY:
        raise RuntimeError("unexpected Search integration predecessor")

    before = FAMILY.read_bytes()
    updated = reconciled_family(before, sha(DISPATCH))
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(FAMILY, CHECKPOINT / "family-manifest.json.before")
    try:
        atomic_write(FAMILY, updated)
        installed = json.loads(FAMILY.read_text())
        if installed["skin"]["tools/select_dispatch.py"] != sha(DISPATCH):
            raise RuntimeError("Search dispatcher acceptance mismatch")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        atomic_write(FAMILY, before)
        RECOVERY.write_text("r41 Search-manifest rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "dispatcher_sha256": sha(DISPATCH),
        "family_manifest_sha256": sha(FAMILY),
        "search_acceptance_matches": True,
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
