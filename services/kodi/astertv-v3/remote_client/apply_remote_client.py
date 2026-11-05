#!/usr/bin/env python3
"""Reapply only the accepted Aster Remote client before Jen's Kodi starts."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket


HOST = "AsterTV-Jen"
STABLE = Path("/storage/.aster-v3/m8/service.asterremote")
TARGET = Path("/storage/.kodi/addons/service.asterremote")
MANIFEST = Path("/storage/.aster-v3/m8/manifest.json")
KEY = Path("/storage/.aster-private/asterremote-client.key")


def digest(path):
    value = hashlib.sha256()
    for item in sorted(row for row in Path(path).rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0")
        value.update(item.read_bytes())
    return value.hexdigest()


def main():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if not KEY.is_file() or KEY.stat().st_mode & 0o077:
        raise RuntimeError("remote-client-key-boundary")
    report = json.loads(MANIFEST.read_text())
    if report != {"schema": 1, "addon_sha256": digest(STABLE)}:
        raise RuntimeError("remote-client-manifest-drift")
    staging = TARGET.with_name("." + TARGET.name + ".installing")
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(STABLE, staging)
    if TARGET.exists():
        shutil.rmtree(TARGET)
    os.replace(staging, TARGET)
    print(json.dumps({"outcome": "applied", "host": HOST,
                      "credential_output": False}, sort_keys=True))


if __name__ == "__main__":
    main()
