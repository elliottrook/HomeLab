#!/usr/bin/env python3
"""Install the authorized M5B interpreter-custody correction without running it."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import time


PILOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
REGISTRY = PILOT / "lab_hours_workloads.py"
ADAPTER = PILOT / "epub_word_alignment_adapter.py"
MANIFEST = PILOT / "lab_hours_release_manifest.json"
GUEST = "/opt/epub-narration/tools/ebook_word_alignment_benchmark.py"
WORKLOAD = "astertv-v3-ebook-word-alignment-v1"
FAILED_BOOKING = "astertv-v3-m5b-align-20261105-2345"
EXPECTED = {
    REGISTRY: "06dd6a26961e10a8a76bf67d8a9a97d9ecedad261fe3e299fc1b1eb75f44cae5",
    ADAPTER: "a17ff180a2f94a15d078caf56f9456e4ba5d9c132ce816577317b90a9fbeda28",
    MANIFEST: "c3e7cf32d48f81107071139d81a6a06f6829744bfd234c82c6fc0b6ba35442e1",
}
OLD_GUEST_SHA = "24ad4300070c703068731192fac2502220a552f6acdc99d6d2a228205a997b92"
NEW_GUEST_SHA = "04fb4971b13cf803957c1cce501035be2583607ab7727e095d2fbf8130d5b04e"
NEW_ADAPTER_SHA = "8df7f426c941d043e5e69b1c1ba8f214d479750793c5e0d6cd7551c3af15e29e"
CHECKPOINT_ROOT = Path("/var/lib/local-ai-lab/checkpoints")


class RepairError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, expected: str | None = None, *, expected_uid: int = 0) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink() or info.st_uid != expected_uid
            or info.st_nlink != 1 or info.st_size > 2 * 1024 * 1024):
        raise RepairError("SOURCE_CUSTODY")
    value = path.read_bytes()
    if expected and digest(value) != expected:
        raise RepairError("SOURCE_DRIFT:" + path.name)
    return value


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.m5b-", dir=path.parent)
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


def command(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)


def build(stage: Path, *, expected_uid: int = 0) -> dict[Path, bytes]:
    guest = regular(stage / "ebook_word_alignment_benchmark.py", NEW_GUEST_SHA,
                    expected_uid=expected_uid)
    adapter = regular(stage / "epub_word_alignment_adapter.py", NEW_ADAPTER_SHA,
                      expected_uid=expected_uid)
    live = {path: regular(path, expected, expected_uid=expected_uid)
            for path, expected in EXPECTED.items()}
    if NEW_GUEST_SHA.encode() not in adapter or OLD_GUEST_SHA.encode() in adapter:
        raise RepairError("GUEST_PIN_NOT_BOUND")
    registry = live[REGISTRY].decode()
    if registry.count(EXPECTED[ADAPTER]) != 1:
        raise RepairError("REGISTRY_PIN_ANCHOR")
    registry_bytes = registry.replace(EXPECTED[ADAPTER], NEW_ADAPTER_SHA).encode()
    manifest = json.loads(live[MANIFEST])
    pins = manifest.get("pins")
    if (not isinstance(pins, dict) or pins.get(ADAPTER.name) != EXPECTED[ADAPTER]
            or pins.get(REGISTRY.name) != EXPECTED[REGISTRY]):
        raise RepairError("MANIFEST_PIN_ANCHOR")
    pins[ADAPTER.name] = NEW_ADAPTER_SHA
    pins[REGISTRY.name] = digest(registry_bytes)
    manifest_bytes = (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()
    return {REGISTRY: registry_bytes, ADAPTER: adapter, MANIFEST: manifest_bytes,
            Path(GUEST): guest}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--install", action="store_true")
    args = parser.parse_args(argv)
    if os.geteuid() != 0 or os.uname().nodename != "proxmox":
        raise SystemExit("PROXMOX_ROOT_REQUIRED")
    output = build(args.stage)
    if not args.install:
        print(json.dumps({"state": "validated", "effects": "not-attempted",
                          "files": len(output)}, sort_keys=True))
        return 0
    if json.loads(command("/usr/local/sbin/local-ai-lease", "status").stdout) != {"state": "ready"}:
        raise RepairError("LEASE_NOT_READY")
    if command("pct", "exec", "116", "--", "systemctl", "is-active",
               "epub-narration-worker.service").returncode == 0:
        raise RepairError("WORKER_ACTIVE")
    booking = command("/usr/local/sbin/aster-lab-hours", "get", FAILED_BOOKING)
    if booking.returncode or json.loads(booking.stdout).get("state") != "failed":
        raise RepairError("FAILED_ATTEMPT_NOT_RETAINED")
    checkpoint = CHECKPOINT_ROOT / (
        "astertv-v3-m5b-interpreter-custody-" + time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    checkpoint.mkdir(mode=0o700, parents=True)
    for path in EXPECTED:
        shutil.copy2(path, checkpoint / path.name)
        (checkpoint / path.name).chmod(0o600)
    old_guest = checkpoint / "ebook_word_alignment_benchmark.py"
    pulled = command("pct", "pull", "116", GUEST, str(old_guest))
    if pulled.returncode or digest(old_guest.read_bytes()) != OLD_GUEST_SHA:
        raise RepairError("GUEST_CHECKPOINT")
    old_guest.chmod(0o600)
    try:
        for path in (REGISTRY, ADAPTER, MANIFEST):
            atomic_write(path, output[path])
        staged = Path("/tmp/astertv-v3-m5b-guest-interpreter.py")
        atomic_write(staged, output[Path(GUEST)], 0o600)
        pushed = command("pct", "push", "116", str(staged), GUEST, "--perms", "0755")
        staged.unlink()
        if pushed.returncode:
            raise RepairError("GUEST_INSTALL")
        checks = (
            command("python3", "-B", "-m", "py_compile", str(REGISTRY), str(ADAPTER)),
            command("pct", "exec", "116", "--", "/opt/whisper-bench/bin/python",
                    "-m", "py_compile", GUEST),
            command("pct", "exec", "116", "--", "sha256sum", GUEST),
        )
        if (any(item.returncode for item in checks)
                or checks[-1].stdout.strip() != f"{NEW_GUEST_SHA}  {GUEST}"):
            raise RepairError("STATIC_VALIDATION")
    except BaseException:
        for path in EXPECTED:
            shutil.copy2(checkpoint / path.name, path)
        command("pct", "push", "116", str(old_guest), GUEST, "--perms", "0755")
        raise
    print(json.dumps({"state": "installed-inactive", "workload": WORKLOAD,
                      "checkpoint": str(checkpoint), "booking_created": False,
                      "workload_started": False}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RepairError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"state": "no_go", "code": str(error)}, sort_keys=True))
        raise SystemExit(1)
