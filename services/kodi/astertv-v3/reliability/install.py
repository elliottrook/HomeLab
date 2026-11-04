#!/usr/bin/env python3
"""Install the AsterTV reliability service and accept the current runtime.

Run locally on an AsterTV client while Kodi is stopped.  The installer is
host-bound, checkpointed, and idempotent.  It never touches userdata.
"""

import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ALLOWED_HOSTS = {"AsterTV-Family", "AsterTV-Bedroom"}
STAGE = Path(__file__).resolve().parent
ADDONS = Path("/storage/.kodi/addons")
TARGET = ADDONS / "service.aster.reliability"
RELEASE = Path("/storage/.aster-release")
UNIT_DIR = Path("/storage/.config/system.d")
UNIT = UNIT_DIR / "astertv-release-guard.service"
SNAPSHOT_EXTRA_ARGS = ()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_copy(source, target, mode=None):
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + target.name + "-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(source.read_bytes())
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode if mode is not None else source.stat().st_mode & 0o777)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write(target, data, mode):
    target.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix="." + target.name + "-", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def copy_tree(source, target):
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if path.is_symlink():
            raise ValueError("staged-symlink")
        if path.is_dir():
            (target / relative).mkdir(mode=0o755, parents=True, exist_ok=True)
        elif path.is_file():
            atomic_copy(path, target / relative)


def main():
    host = socket.gethostname()
    if host not in ALLOWED_HOSTS:
        raise SystemExit("host-not-authorized")
    if subprocess.run(["systemctl", "is-active", "--quiet", "kodi"], check=False).returncode == 0:
        raise SystemExit("kodi-must-be-stopped")

    checkpoint = Path("/storage/.aster-checkpoints") / (
        "astertv-reliability-" + host + "-" + str(time.time_ns()))
    checkpoint.mkdir(mode=0o700, parents=True)
    if TARGET.exists():
        shutil.copytree(TARGET, checkpoint / TARGET.name)
    if UNIT.exists():
        shutil.copy2(UNIT, checkpoint / UNIT.name)

    copy_tree(STAGE / "service.aster.reliability", TARGET)
    RELEASE.mkdir(mode=0o700, parents=True, exist_ok=True)
    atomic_copy(STAGE / "release_guard.py", RELEASE / "release_guard.py", 0o700)
    UNIT_DIR.mkdir(mode=0o755, parents=True, exist_ok=True)
    unit_data = (STAGE / "astertv-release-guard.service").read_bytes()
    marker = b"--host %H"
    if unit_data.count(marker) != 1:
        raise RuntimeError("release-guard-unit-host-marker")
    # LibreELEC can expose its distribution hostname while early boot units
    # are expanded, before the configured Kodi hostname is applied. The host
    # has already passed the strict allow-list above, so bind the unit to that
    # literal identity instead of relying on systemd's boot-time %H value.
    unit_data = unit_data.replace(marker, b"--host " + host.encode("ascii"))
    atomic_write(UNIT, unit_data, 0o644)

    result = subprocess.run([
        sys.executable, str(RELEASE / "release_guard.py"), "snapshot",
        "--host", host,
        *SNAPSHOT_EXTRA_ARGS,
    ], check=True, capture_output=True, text=True)
    verification = subprocess.run([
        sys.executable, str(RELEASE / "release_guard.py"), "verify",
        "--host", host,
    ], check=True, capture_output=True, text=True)
    # Enable the boot hook only after a complete accepted payload has been
    # written and independently verified. A failed install must not leave a
    # guard pointing at an incomplete baseline.
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "astertv-release-guard.service"], check=True)
    report = {
        "host": host,
        "checkpoint": str(checkpoint),
        "service_py_sha256": sha(TARGET / "service.py"),
        "release_guard_sha256": sha(RELEASE / "release_guard.py"),
        "snapshot": json.loads(result.stdout),
        "verification": json.loads(verification.stdout),
    }
    (checkpoint / "install-report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
