#!/usr/bin/env python3
"""Install or roll back Jen's M6 camera boot-lifecycle correction."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess


HOST = "AsterTV-Jen"
UNIT = "aster-camera.service"
LIVE = Path("/storage/.aster-v3/m6/apply_jen_home_cameras.py")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v3-m6-camera-on-demand-r1")
PREDECESSOR = "4aad7acccf815ad515a1b6dfb847305656403ff695a88c6a80b34e11a1c75432"


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def state(name):
    return run("systemctl", "is-" + name, UNIT, check=False).stdout.strip()


def preflight():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    if sha(LIVE) != PREDECESSOR:
        raise RuntimeError("predecessor-drift")


def checkpoint():
    if CHECKPOINT.exists():
        report = json.loads((CHECKPOINT / "checkpoint.json").read_text())
        saved = CHECKPOINT / "apply_jen_home_cameras.py"
        if report.get("host") != HOST or sha(saved) != report.get("sha256"):
            raise RuntimeError("checkpoint-drift")
        return
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    saved = CHECKPOINT / "apply_jen_home_cameras.py"
    shutil.copy2(LIVE, saved)
    report = {
        "schema": 1,
        "host": HOST,
        "sha256": sha(saved),
        "unit_enabled": state("enabled") == "enabled",
        "unit_active": state("active") == "active",
    }
    metadata = CHECKPOINT / "checkpoint.json"
    metadata.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(metadata, 0o600)


def atomic_copy(source, destination):
    temporary = destination.with_name("." + destination.name + ".m6-camera")
    shutil.copy2(source, temporary)
    os.chmod(temporary, 0o600)
    os.replace(temporary, destination)


def install(source):
    preflight()
    checkpoint()
    atomic_copy(source, LIVE)
    run("systemctl", "disable", "--now", UNIT)
    if state("enabled") != "disabled" or state("active") != "inactive":
        raise RuntimeError("camera-unit-not-quiescent")
    print(json.dumps({"outcome": "installed", "unit": UNIT}, sort_keys=True))


def rollback():
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("AsterTV-Jen-root-only")
    report = json.loads((CHECKPOINT / "checkpoint.json").read_text())
    saved = CHECKPOINT / "apply_jen_home_cameras.py"
    if report.get("host") != HOST or sha(saved) != report.get("sha256"):
        raise RuntimeError("checkpoint-drift")
    atomic_copy(saved, LIVE)
    run("systemctl", "enable" if report["unit_enabled"] else "disable", UNIT)
    run("systemctl", "start" if report["unit_active"] else "stop", UNIT)
    if sha(LIVE) != PREDECESSOR:
        raise RuntimeError("rollback-drift")
    print(json.dumps({"outcome": "rolled-back", "unit": UNIT}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source", type=Path)
    group.add_argument("--rollback", action="store_true")
    args = parser.parse_args()
    rollback() if args.rollback else install(args.source)


if __name__ == "__main__":
    main()
