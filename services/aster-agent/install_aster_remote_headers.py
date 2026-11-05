#!/usr/bin/env python3
"""Checkpoint and install/rollback Aster Remote browser security headers."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import shutil
import socket
import subprocess
import time
import urllib.request


HOST = "hermesagent"
TARGET = Path("/opt/aster-agent/aster_remote.py")
CHECKPOINT = Path("/var/lib/aster/checkpoints/astertv-v3-m8-jen/post-install/aster_remote.py")
OLD = "e78f659d409f42053d597fc9005d0afd52f93e171324041f53c19b8a449a4f1e"
NEW = "17d7e1f0f76f284195e8ac82cbc7e3a222ebd6d7704bc5ed86b6a9d691b16eba"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def wait_headers(expected):
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/remote/", timeout=3) as reply:
                present = reply.headers.get("Content-Security-Policy") is not None
                if reply.status == 200 and present is expected:
                    return
        except OSError:
            pass
        time.sleep(0.25)
    raise RuntimeError("header-validation-failed")


def install(source):
    if socket.gethostname() != HOST or sha(TARGET) != OLD or sha(source) != NEW:
        raise RuntimeError("header-install-boundary")
    if CHECKPOINT.exists():
        raise RuntimeError("header-checkpoint-exists")
    CHECKPOINT.parent.mkdir(parents=True, mode=0o700)
    shutil.copy2(TARGET, CHECKPOINT)
    if sha(CHECKPOINT) != OLD:
        raise RuntimeError("header-checkpoint-drift")
    run("systemctl", "stop", "aster-agent")
    try:
        shutil.copy2(source, TARGET)
        run("systemctl", "start", "aster-agent")
        wait_headers(True)
    except Exception:
        shutil.copy2(CHECKPOINT, TARGET)
        run("systemctl", "start", "aster-agent", check=False)
        raise


def rollback():
    if socket.gethostname() != HOST or sha(TARGET) != NEW or sha(CHECKPOINT) != OLD:
        raise RuntimeError("header-rollback-boundary")
    run("systemctl", "stop", "aster-agent")
    shutil.copy2(CHECKPOINT, TARGET)
    run("systemctl", "start", "aster-agent")
    wait_headers(False)


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--source", type=Path)
group.add_argument("--rollback", action="store_true")
args = parser.parse_args()
rollback() if args.rollback else install(args.source)
