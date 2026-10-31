#!/usr/bin/env python3
"""Render the shared Books navigation rail above all Books content layers."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
SKIN = ROOT / "skin.asterhome"
RUNTIME = ROOT / "script.asterruntime"
BOOKS = SKIN / "1080i/IncludesBooks.xml"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-books-rail-r17-20261030")
EXPECTED = {
    BOOKS: "dcf465aeb3fbbd6f48a36b92f7d8fe2d60e8289233384d57c7e92181326461e9",
    FAMILY: "eb25e3fbbad9496694d0a3e8fd9f95375c30b88e726baca55968b2c1ae4445a8",
}


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
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r17-", dir=path.parent)
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


def candidates(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    books_text = originals[BOOKS].decode()
    rail = ('      <include content="AsterNavigationRail"><param name="content" '
            'value="500" /><param name="railfocus" value="9002" /></include>')
    if books_text.count(rail) != 1:
        raise RuntimeError("Books rail source count")
    books_text = books_text.replace(rail, "", 1)
    marker = "    </definition>\n  </include>\n  <include name=\"AsterBooksHomeRow\">"
    if books_text.count(marker) != 1:
        raise RuntimeError("Books definition close marker")
    # Kodi 22 does not reliably honour a group's zorder across an earlier
    # expanded include. Rendering the shared rail last keeps every book row,
    # heading and hero beneath the complete rail surface.
    books_text = books_text.replace(
        marker,
        "      " + rail.strip() + "\n" + marker,
        1,
    )
    if books_text.rfind("AsterNavigationRail") < books_text.rfind('id="139"'):
        raise RuntimeError("Books rail is not topmost")
    books = books_text.encode()
    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/IncludesBooks.xml"] = sha(books)
    return {BOOKS: books, FAMILY: encoded(family)}


def main() -> None:
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    changed = candidates(originals)
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-books-rail-r17", "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(originals[path])
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(originals[path]), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in changed.items():
            atomic_write(path, candidate)
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, original in originals.items():
            atomic_write(path, original)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in changed.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
