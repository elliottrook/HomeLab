#!/usr/bin/env python3
"""Reapply an accepted Family/Bedroom Remote client before Kodi starts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket


HOSTS = {"AsterTV-Family", "AsterTV-Bedroom"}
STABLE = Path("/storage/.aster-v3/m8-remote/service.asterremote")
TARGET = Path("/storage/.kodi/addons/service.asterremote")
MANIFEST = Path("/storage/.aster-v3/m8-remote/manifest.json")
KEY = Path("/storage/.aster-private/asterremote-client.key")
CONFIG = Path("/storage/.aster-private/asterremote-client.json")


def digest(path):
    value = hashlib.sha256()
    for item in sorted(row for row in Path(path).rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0")
        value.update(item.read_bytes())
    return value.hexdigest()


def main():
    host = socket.gethostname()
    if host not in HOSTS or os.getuid() != 0: raise RuntimeError("room-root-only")
    for path in (KEY, CONFIG):
        if not path.is_file() or path.stat().st_mode & 0o077:
            raise RuntimeError("remote-client-private-boundary")
    if json.loads(MANIFEST.read_text()) != {"schema": 1, "addon_sha256": digest(STABLE)}:
        raise RuntimeError("remote-client-manifest-drift")
    staging = TARGET.with_name("." + TARGET.name + ".installing")
    if staging.exists(): shutil.rmtree(staging)
    shutil.copytree(STABLE, staging)
    if TARGET.exists(): shutil.rmtree(TARGET)
    os.replace(staging, TARGET)
    print(json.dumps({"outcome": "applied", "host": host, "credential_output": False}))


if __name__ == "__main__": main()
