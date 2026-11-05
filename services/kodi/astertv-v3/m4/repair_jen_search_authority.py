#!/usr/bin/env python3
"""Repair Jen's M4 dispatcher authority pin without changing dispatcher code."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile


HOST = "AsterTV-Jen"
STABLE = Path("/storage/.aster-v3/m4/install_jen_movie.py")
FAMILY = Path("/storage/.kodi/addons/script.asterruntime/family-manifest.json")
DISPATCH = Path("/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m8-jen-search-authority")
OLD_INSTALLER = "6537defd4161deae9f7cabf4e269b04a0c33ffd128cca38f595ce2346213b2b9"
NEW_INSTALLER = "09b08a7ee67c50c3d97759b3ce96c42f0c2572fb158f54ce23eba068997f17fe"
CURRENT_FAMILY = "185a17e5a92ff2a044de203867468e7a4146a285ca995e5e413daaf4b1483c86"
DISPATCH_SHA = "d72d82630a5b0a172f5c8ba7b11d51ad04cadb80500fbcfbd48da9d7374397e3"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, data, mode):
    handle, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(data); output.flush(); os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install(source):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if any((sha(STABLE) != OLD_INSTALLER, sha(source) != NEW_INSTALLER,
            sha(FAMILY) != CURRENT_FAMILY, sha(DISPATCH) != DISPATCH_SHA)):
        raise RuntimeError("search-authority-boundary")
    if CHECKPOINT.exists():
        raise RuntimeError("search-authority-checkpoint-exists")
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    shutil.copy2(STABLE, CHECKPOINT / "install_jen_movie.py")
    shutil.copy2(FAMILY, CHECKPOINT / "family-manifest.json")
    data = json.loads(FAMILY.read_text())
    prior = data["skin"].get("tools/select_dispatch.py")
    if prior == DISPATCH_SHA:
        raise RuntimeError("search-authority-already-current")
    data["skin"]["tools/select_dispatch.py"] = DISPATCH_SHA
    payload = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    try:
        shutil.copy2(source, STABLE)
        atomic(FAMILY, payload, FAMILY.stat().st_mode & 0o777)
        if sha(STABLE) != NEW_INSTALLER:
            raise RuntimeError("stable-installer-validation")
        installed = json.loads(FAMILY.read_text())
        if installed["skin"]["tools/select_dispatch.py"] != sha(DISPATCH):
            raise RuntimeError("search-authority-validation")
    except Exception:
        shutil.copy2(CHECKPOINT / "install_jen_movie.py", STABLE)
        shutil.copy2(CHECKPOINT / "family-manifest.json", FAMILY)
        raise
    print(json.dumps({"outcome": "repaired", "host": HOST,
                      "dispatcher_changed": False}, sort_keys=True))


def rollback():
    if socket.gethostname() != HOST or sha(STABLE) != NEW_INSTALLER:
        raise RuntimeError("search-authority-rollback-boundary")
    if sha(CHECKPOINT / "install_jen_movie.py") != OLD_INSTALLER or sha(
            CHECKPOINT / "family-manifest.json") != CURRENT_FAMILY:
        raise RuntimeError("search-authority-checkpoint-drift")
    shutil.copy2(CHECKPOINT / "install_jen_movie.py", STABLE)
    shutil.copy2(CHECKPOINT / "family-manifest.json", FAMILY)
    print(json.dumps({"outcome": "rolled-back", "host": HOST}, sort_keys=True))


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
args = parser.parse_args()
rollback() if args.rollback else install(args.source)
