"""Fixed Proxmox bridge for one SA4 LXC observer-proof exchange."""
from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
from typing import Callable

import sa4_observer_signer_v1 as observer


PCT = "/usr/sbin/pct"
VMID = "104"
LXC_DIRECTORY = "/run/aster-sa4-observer-exchange"
BRIDGE_DIRECTORY = Path("/run/aster-sa4-observer-bridge")
EXPECTED_UID = 0


def _directory() -> None:
    metadata = BRIDGE_DIRECTORY.lstat()
    if (not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != EXPECTED_UID
            or stat.S_IMODE(metadata.st_mode) != 0o700):
        raise ValueError("SA4 observer bridge directory changed")


def _write_exclusive(path: Path, raw: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        if os.write(descriptor, raw) != len(raw):
            raise OSError("short SA4 observer bridge write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def bridge(sequence: int, *,
           runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
           signer: Callable[[bytes], str] = observer.sign) -> dict[str, object]:
    if type(sequence) is not int or sequence not in (1, 2):
        raise ValueError("SA4 observer bridge sequence changed")
    _directory()
    request = BRIDGE_DIRECTORY / f"request-{sequence}.json"
    response = BRIDGE_DIRECTORY / f"response-{sequence}.signature"
    if request.exists() or response.exists():
        raise FileExistsError("SA4 observer bridge sequence already exists")
    pulled = runner([
        PCT, "pull", VMID, f"{LXC_DIRECTORY}/request-{sequence}.json",
        str(request), "--perms", "0600"], capture_output=True, check=False,
        timeout=15)
    if pulled.returncode != 0:
        raise RuntimeError("SA4 observer request pull failed")
    statement = observer.read_statement(str(request))
    signature = signer(statement)
    if not isinstance(signature, str) or len(signature) != 512:
        raise ValueError("SA4 observer bridge signature shape changed")
    _write_exclusive(response, signature.encode("ascii") + b"\n")
    pushed = runner([
        PCT, "push", VMID, str(response),
        f"{LXC_DIRECTORY}/response-{sequence}.signature",
        "--perms", "0600", "--user", "0", "--group", "0"],
        capture_output=True, check=False, timeout=15)
    if pushed.returncode != 0:
        raise RuntimeError("SA4 observer response push failed")
    return {
        "schema": "aster-sa4-observer-bridge-result.v1",
        "sequence": sequence,
        "request_validated": True,
        "signature_written": True,
        "arbitrary_command": False,
    }
