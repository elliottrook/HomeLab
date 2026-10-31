#!/usr/bin/env python3
"""Restore Search's missing details reader and reconcile both integrity manifests."""
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
DEFAULT = SEARCH / "default.py"
MANIFEST = SEARCH / "manifest.json"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-search-details-r42-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED = {
    DEFAULT: "907049cbbf0509ad3989373c10691b9c1deba9f778c88f2ab9fe23a61ba5de71",
    MANIFEST: "194c992d7632a67f3733ffc1d302b62ee5756a8697d212d87aea3ba23d4b5b37",
    FAMILY: "613e2333a0805ebb20d7a52f3e513d21c6dbaf785812a212ac225ea192371e44",
}
IMPORT_ANCHOR = (
    "from global_search import SOURCES,READS,SearchUnavailable,search_group,normalize_query\n"
)
DETAILS_IMPORT = "from search_details import read_details\n"


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


def patched(default: bytes, manifest: bytes, family: bytes):
    text = default.decode()
    if DETAILS_IMPORT in text or text.count(IMPORT_ANCHOR) != 1:
        raise RuntimeError("unexpected Search import predecessor")
    new_default = text.replace(
        IMPORT_ANCHOR, IMPORT_ANCHOR + DETAILS_IMPORT, 1).encode()
    compile(new_default, str(DEFAULT), "exec")

    component = json.loads(manifest)
    row = next((item for item in component.get("files", [])
                if item.get("path") == "default.py"), None)
    if row is None or row.get("sha256") != digest(default):
        raise RuntimeError("Search manifest predecessor mismatch")
    row["bytes"] = len(new_default)
    row["sha256"] = digest(new_default)
    new_manifest = encode(component)

    accepted = json.loads(family)
    component_row = accepted.get("components", {}).get(
        "aster-global-search-ui22", {})
    if component_row.get("manifest_sha256") != digest(manifest):
        raise RuntimeError("family manifest predecessor mismatch")
    component_row["manifest_sha256"] = digest(new_manifest)
    return new_default, new_manifest, encode(accepted)


def atomic_write(path: Path, data: bytes, mode: int) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r42-", dir=path.parent)
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
    updated = patched(before[DEFAULT], before[MANIFEST], before[FAMILY])
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path in EXPECTED:
        shutil.copy2(path, CHECKPOINT / (path.name + ".before"))
    try:
        for path, data, mode in zip(
                (DEFAULT, MANIFEST, FAMILY), updated, (0o755, 0o644, 0o644)):
            atomic_write(path, data, mode)
        installed_manifest = json.loads(MANIFEST.read_text())
        installed_family = json.loads(FAMILY.read_text())
        default_row = next(item for item in installed_manifest["files"]
                           if item["path"] == "default.py")
        if default_row["sha256"] != sha(DEFAULT):
            raise RuntimeError("installed Search manifest mismatch")
        if (installed_family["components"]["aster-global-search-ui22"]
                ["manifest_sha256"] != sha(MANIFEST)):
            raise RuntimeError("installed family manifest mismatch")
        if rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("unexpected active player")
    except Exception:
        for path in (DEFAULT, MANIFEST, FAMILY):
            atomic_write(path, before[path], 0o755 if path == DEFAULT else 0o644)
        RECOVERY.write_text("r42 Search-details rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "default_sha256": sha(DEFAULT),
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
