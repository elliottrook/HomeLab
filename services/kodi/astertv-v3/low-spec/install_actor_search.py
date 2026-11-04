#!/usr/bin/env python3
"""Install the exact production actor-search add-on on AsterTV-Jen."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


SOURCE = Path("/storage/.aster-staging/plugin.video.astersearch")
TARGET = Path("/storage/.kodi/addons/plugin.video.astersearch")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-jen-actor-search-20261104")
EXPECTED = {
    "addon.xml": "80ab9ffde1a06e3938825a37751aa0b1efbd8ac0dc8863bc438124938c3cdd85",
    "actor_search.py": "3af636f47623514d69e3aa8480a0de91f048eeb629c029fc8cc2d486b515a39c",
    "default.py": "6353c1473f25bd6b46fb37894e01ed101c89771f32dbf352d145debc9bcf97aa",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(value):
    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", 9090), timeout=1) as client:
                client.settimeout(3)
                client.sendall((json.dumps(value) + "\n").encode())
                return json.loads(client.recv(4096))
        except (OSError, ValueError, json.JSONDecodeError):
            time.sleep(0.5)
    raise RuntimeError("actor-search-jsonrpc")


def main():
    if socket.gethostname() != "AsterTV-Jen" or os.getuid() != 0:
        raise RuntimeError("actor-search-target")
    if TARGET.exists() or CHECKPOINT.exists():
        raise RuntimeError("actor-search-install-state")
    files = {str(path.relative_to(SOURCE)): path for path in SOURCE.rglob("*") if path.is_file()}
    if set(files) != set(EXPECTED) or any(sha(files[name]) != digest for name, digest in EXPECTED.items()):
        raise RuntimeError("actor-search-source")
    for path in files.values():
        if path.is_symlink():
            raise RuntimeError("actor-search-source-link")
        compile(path.read_bytes(), str(path), "exec") if path.suffix == ".py" else None
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "host": "AsterTV-Jen", "files": EXPECTED, "target_absent": True,
    }, indent=2, sort_keys=True) + "\n")
    os.chmod(CHECKPOINT / "manifest.json", 0o600)
    try:
        subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=90)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        state = subprocess.run(
            ["systemctl", "is-active", "kodi"], check=False,
            capture_output=True, text=True, timeout=5).stdout.strip()
        if state not in {"inactive", "failed"}:
            raise
    try:
        shutil.copytree(SOURCE, TARGET)
        if any(sha(TARGET / name) != digest for name, digest in EXPECTED.items()):
            raise RuntimeError("actor-search-install-hash")
    except Exception:
        shutil.rmtree(TARGET, ignore_errors=True)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    answer = rpc({"jsonrpc": "2.0", "id": 1, "method": "Addons.SetAddonEnabled",
                  "params": {"addonid": "plugin.video.astersearch", "enabled": True}})
    if answer.get("result") != "OK":
        raise RuntimeError("actor-search-enable")
    print(json.dumps({"installed": True, "files": len(EXPECTED),
                      "checkpoint": str(CHECKPOINT)}, sort_keys=True))


if __name__ == "__main__":
    main()
