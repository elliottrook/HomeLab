#!/usr/bin/env python3
"""Restore the external narrated-book data links omitted from production."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket


CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-ebook-data-link-r23-20261030")
TARGET = Path("/storage/aster-reader")
LINKS = (
    Path("/storage/.aster-staging/aster-books-compiler-reader-v1/data"),
    Path("/storage/.aster-staging/aster-epub-consumer1/reader/data"),
)


def rpc(method: str):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if (not TARGET.is_dir() or TARGET.is_symlink()
            or not (TARGET / "ready").is_dir() or not (TARGET / "generations").is_dir()):
        raise RuntimeError("narration output unavailable")
    for link in LINKS:
        if link.exists() or link.is_symlink() or not link.parent.is_dir():
            raise RuntimeError("unexpected data link state: " + str(link))

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-production-ebook-data-link-r23",
        "target": str(TARGET),
        "links_before": "absent",
        "links": [str(link) for link in LINKS],
    }, indent=2, sort_keys=True) + "\n")
    created = []
    try:
        for link in LINKS:
            link.symlink_to(TARGET, target_is_directory=True)
            created.append(link)
        for link in LINKS:
            if not link.is_symlink() or link.resolve(strict=True) != TARGET.resolve(strict=True):
                raise RuntimeError("data link verification failed: " + str(link))
    except Exception:
        for link in reversed(created):
            if link.is_symlink() and os.readlink(link) == str(TARGET):
                link.unlink()
        raise
    print(json.dumps({
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "target": str(TARGET),
        "links": [str(link) for link in LINKS],
        "active_players": rpc("Player.GetActivePlayers"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
