#!/usr/bin/env python3
"""Migrate the pinned Aster Books reader boundary after final host renaming."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile


COMPILER = Path("/storage/.aster-staging/aster-books-compiler-reader-v1")
CONSUMER = Path("/storage/.aster-staging/aster-epub-consumer1")
ACTIVATION = Path("/storage/.aster-state/aster-books-compiler-reader-v1/activation.json")
RECOVERY_GUARD = Path("/storage/.aster-recovery-required")
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")
FILES = (
    COMPILER / "default.py",
    COMPILER / "bundle.json",
    CONSUMER / "reader/default.py",
    CONSUMER / "reader/bundle.json",
    CONSUMER / "manifest.json",
    ACTIVATION,
)
EXPECTED = {
    COMPILER / "default.py": "a1cf49181186183c45217676330443dcf3248a8bc462bba07f2a7ded1cd6cf38",
    COMPILER / "bundle.json": "d41eddcd7fe754eba6d00677e17aa0a69c2dd10991b434586fc6aa4578bc6f89",
    CONSUMER / "reader/default.py": "a1cf49181186183c45217676330443dcf3248a8bc462bba07f2a7ded1cd6cf38",
    CONSUMER / "reader/bundle.json": "d41eddcd7fe754eba6d00677e17aa0a69c2dd10991b434586fc6aa4578bc6f89",
    CONSUMER / "manifest.json": "8450cb265d9a5f9b3d041ad9d6cf8fd643f3fd7c5320cb3a933146353d02ea4e",
    ACTIVATION: "8c7d8441617c67986fe0593010645e5b48fbe7df1406d97cc4b57e10cc7806b7",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
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
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-books-identity-", dir=path.parent)
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
    host = os.uname().nodename
    if host not in ("AsterTV-Bedroom", "AsterTV-Family"):
        raise RuntimeError("AsterTV Family/Bedroom host only")
    if RECOVERY_GUARD.exists():
        raise RuntimeError("recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")

    originals = {path: path.read_bytes() for path in FILES}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))

    defaults = {}
    old = 'require(os.uname().nodename == "AsterTV" and len(sys.argv) == 3, "books-hp-only")'
    new = ('require(os.uname().nodename in ("AsterTV-Bedroom", "AsterTV-Family") '
           'and len(sys.argv) == 3, "books-aster-client-only")')
    for path in (COMPILER / "default.py", CONSUMER / "reader/default.py"):
        text = originals[path].decode()
        if text.count(old) != 1:
            raise RuntimeError("reader identity source mismatch")
        data = text.replace(old, new, 1).encode()
        compile(data, str(path), "exec")
        defaults[path] = data

    bundles = {}
    for path, default in ((COMPILER / "bundle.json", defaults[COMPILER / "default.py"]),
                          (CONSUMER / "reader/bundle.json",
                           defaults[CONSUMER / "reader/default.py"])):
        value = json.loads(originals[path])
        if value.get("hp_only") is not True:
            raise RuntimeError("unexpected reader boundary")
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

    checkpoint = CHECKPOINT_ROOT / ("aster-books-identity-" + host)
    checkpoint.mkdir(mode=0o700, parents=True, exist_ok=False)
    for path, data in originals.items():
        saved = checkpoint / (str(path).lstrip("/").replace("/", "__") + ".before")
        saved.write_bytes(data)
        saved.chmod(0o600)
    (checkpoint / "manifest.json").write_text(json.dumps({
        "kind": "aster-books-final-host-identity",
        "host": host,
        "files": {str(path): {"before": sha(originals[path]),
                              "after": sha(candidates[path])}
                  for path in FILES},
    }, indent=2, sort_keys=True) + "\n")

    try:
        for path, data in candidates.items():
            atomic_write(path, data)
        for path, data in candidates.items():
            if path.read_bytes() != data:
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, data in originals.items():
            atomic_write(path, data)
        raise

    print(json.dumps({
        "changed": True,
        "checkpoint": str(checkpoint),
        "host": host,
        "bundle_sha256": sha(bundles[COMPILER / "bundle.json"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
