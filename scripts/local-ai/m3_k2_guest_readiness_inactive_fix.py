"""Install the bounded K2 guest-custody readiness correction inactive."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess


ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path(
    "/var/lib/local-ai-lab/checkpoints/m3-k2-guest-readiness-20261106"
)
BOOKING = "aster-stream-a-m3-k2-20261106-2000-r1"
FILES = {
    "lab_hours_workloads.py": (
        "e8a93e05c23c8bddcb329c0025963639a18926904455d11261bd28e2f5d2b4d9",
        "5977a5f7c66ba12a7400d6e19233b7dc3ec7e5c7541f90c1b57c5436acc62a1c"),
    "lab_hours_release_manifest.json": (
        "555bb3ab2a976f521f74c3b866397ec3cab04ae49fbe494872dfc7ffe69d880d",
        "6131083a41a1fb1a1722d758585060b486ac081bc179150f244ac3d11068054b"),
}


class InstallError(RuntimeError):
    pass


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def regular(path: Path, expected: str) -> bytes:
    info = path.lstat()
    raw = path.read_bytes()
    if (not path.is_file() or path.is_symlink() or info.st_uid != 0
            or info.st_nlink != 1 or info.st_mode & 0o777 != 0o644
            or digest(raw) != expected):
        raise InstallError("BASELINE_OR_SOURCE_DRIFT:" + path.name)
    return raw


def atomic(path: Path, raw: bytes) -> None:
    temporary = path.parent / ("." + path.name + ".k2-readiness")
    if os.path.lexists(temporary):
        raise InstallError("TEMP_EXISTS:" + path.name)
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                         | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, raw)
        os.fchmod(descriptor, 0o644)
        os.fchown(descriptor, 0, 0)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def command(value: tuple[str, ...], timeout: int = 30):
    return subprocess.run(value, capture_output=True, text=True, timeout=timeout,
                          check=False)


def quiet_and_scheduled() -> None:
    lease = command(("/usr/local/sbin/local-ai-lease", "status"), 10)
    try:
        lease_value = json.loads(lease.stdout)
    except json.JSONDecodeError:
        lease_value = None
    if lease.returncode or lease_value not in ("ready", {"state": "ready"}):
        raise InstallError("LEASE_NOT_READY")
    for path in (Path("/run/local-ai-lab-operation.lock"),
                 Path("/var/lib/local-ai-lab/full-inference-drain.lock"),
                 Path("/var/lib/local-ai-lab/full-inference-drain.json")):
        if path.exists():
            raise InstallError("SHARED_STATE_OR_LOCK_PRESENT")
    booking = command(("/usr/local/sbin/aster-lab-hours", "get", BOOKING), 10)
    try:
        value = json.loads(booking.stdout)
    except json.JSONDecodeError as exc:
        raise InstallError("BOOKING_UNREADABLE") from exc
    if (booking.returncode or value.get("state") != "scheduled"
            or value.get("workload")
                != "m3-k2-shortlist-arbitration-development-v1"):
        raise InstallError("BOOKING_NOT_SCHEDULED")


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    quiet_and_scheduled()
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    old = {name: regular(ROOT / name, hashes[0])
           for name, hashes in FILES.items()}
    new = {name: regular(stage / name, hashes[1])
           for name, hashes in FILES.items()}
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    os.chown(CHECKPOINT, 0, 0)
    for name, raw in old.items():
        target = CHECKPOINT / name
        descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                             | os.O_NOFOLLOW, 0o600)
        try:
            os.write(descriptor, raw); os.fsync(descriptor)
        finally:
            os.close(descriptor)
    try:
        for name in FILES:
            atomic(ROOT / name, new[name])
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(ROOT)}
        proof = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_workloads as w,lab_hours_reserved_runner as r;"
            "w.validate_registry();r.load_manifest();"
            "v=w.validate_inactive_target(" + repr(str(ROOT)) + ",workload_id="
            "'m3-k2-shortlist-arbitration-development-v1');"
            "assert v['runtime_location']=='lxc110' and v['runtime_files']==12"),
            env=env, capture_output=True, text=True, timeout=60, check=False)
        if proof.returncode:
            raise InstallError("POSTCHECK:" + proof.stderr.strip()[-240:])
        quiet_and_scheduled()
        return {"state": "installed-inactive", "files": 2,
                "guest_runtime_files": 12, "runtime_location": "lxc110",
                "checkpoint": "retained", "service_restart": False,
                "workload_effect": "not-attempted"}
    except BaseException:
        for name in reversed(tuple(FILES)):
            atomic(ROOT / name, old[name])
        raise


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        print(json.dumps({"state": "source-only"}, sort_keys=True)); return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True)); return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
