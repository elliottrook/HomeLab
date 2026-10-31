#!/usr/bin/env python3
"""Repair the production reader's inconsistent multi-client bundle boundary."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile


CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-ebook-boundary-r22-20261030")
COMPILER = Path("/storage/.aster-staging/aster-books-compiler-reader-v1")
CONSUMER = Path("/storage/.aster-staging/aster-epub-consumer1")
ACTIVATION = Path("/storage/.aster-state/aster-books-compiler-reader-v1/activation.json")
FILES = (
    COMPILER / "default.py",
    COMPILER / "bundle.json",
    CONSUMER / "reader/default.py",
    CONSUMER / "reader/bundle.json",
    CONSUMER / "manifest.json",
    ACTIVATION,
)
EXPECTED = {
    COMPILER / "default.py": "7387cac0e2f7cc27df987865f1dfe7fecd21323552ff4271389663cb39e0cbd4",
    COMPILER / "bundle.json": "cd65c5743d4c9fe50aaeabb40207e5979128df4d55a20c7e0f167cc11230a4ca",
    CONSUMER / "reader/default.py": "7387cac0e2f7cc27df987865f1dfe7fecd21323552ff4271389663cb39e0cbd4",
    CONSUMER / "reader/bundle.json": "cd65c5743d4c9fe50aaeabb40207e5979128df4d55a20c7e0f167cc11230a4ca",
    CONSUMER / "manifest.json": "41e0c87121337268e064fb9f67379f8a520272f4300f8159f13495940ec7d06a",
    ACTIVATION: "5a0c42649e9479f3ab12b7558eed530c5a74b1ea667891ab583ddf3980e45f27",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def rpc(method: str):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r22-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600 if path == ACTIVATION else 0o644)
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
    originals = {path: path.read_bytes() for path in FILES}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))

    defaults = {}
    for path in (COMPILER / "default.py", CONSUMER / "reader/default.py"):
        text = originals[path].decode()
        old = 'and manifest.get("hp_only") is True'
        new = 'and manifest.get("hp_only") is False'
        if text.count(old) != 1:
            raise RuntimeError("reader boundary source mismatch")
        data = text.replace(old, new, 1).encode()
        compile(data, str(path), "exec")
        defaults[path] = data

    bundles = {}
    for path, default in ((COMPILER / "bundle.json", defaults[COMPILER / "default.py"]),
                          (CONSUMER / "reader/bundle.json", defaults[CONSUMER / "reader/default.py"])):
        value = json.loads(originals[path])
        if value.get("hp_only") is not False:
            raise RuntimeError("bundle is not production multi-client")
        value["files"]["default.py"] = sha(default)
        bundles[path] = encoded(value)
    if bundles[COMPILER / "bundle.json"] != bundles[CONSUMER / "reader/bundle.json"]:
        raise RuntimeError("reader bundles diverged")

    consumer = json.loads(originals[CONSUMER / "manifest.json"])
    consumer["files"]["reader/default.py"] = sha(defaults[CONSUMER / "reader/default.py"])
    consumer["files"]["reader/bundle.json"] = sha(bundles[CONSUMER / "reader/bundle.json"])
    consumer["reader_pin"] = sha(bundles[CONSUMER / "reader/bundle.json"])
    consumer_data = encoded(consumer)
    activation = json.loads(originals[ACTIVATION])
    activation["bundle_sha256"] = sha(bundles[COMPILER / "bundle.json"])
    activation_data = encoded(activation)
    candidates = {
        **defaults,
        **bundles,
        CONSUMER / "manifest.json": consumer_data,
        ACTIVATION: activation_data,
    }

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path, data in originals.items():
        saved = CHECKPOINT / (str(path).lstrip("/").replace("/", "__") + ".before")
        saved.write_bytes(data)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-production-ebook-boundary-r22",
        "files": {str(path): {"before": sha(originals[path]), "after": sha(candidates[path])}
                  for path in FILES},
    }, indent=2, sort_keys=True) + "\n")
    try:
        for path, data in candidates.items():
            atomic_write(path, data)
        for path, data in candidates.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, data in originals.items():
            atomic_write(path, data)
        Path("/storage/.aster-recovery-required").write_text("r22 eBook rollback required\n")
        raise
    print(json.dumps({
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "bundle_sha256": sha(bundles[COMPILER / "bundle.json"]),
        "active_players": rpc("Player.GetActivePlayers"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
