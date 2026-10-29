"""Fixed, reversible installation of the inactive SA3 Lab Hours registration."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


TARGET_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-registration-v1")
HOST_UNITS = (
    Path("/etc/systemd/system/aster-lab-hours-booking-sa3-expanded-source-quality-v1.service"),
    Path("/etc/systemd/system/aster-lab-hours-booking-sa3-expanded-source-quality-v1.timer"),
)


class RegistrationInstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class FileSpec:
    name: str
    mode: int
    new_sha256: str
    old_sha256: str | None
    old_mode: int | None


FILES = (
    FileSpec("lab_hours_workloads.py", 0o644,
             "2780fcc7f7638a8d9987c79f2438d92fbc31c106ca67da81c994ca8ccb0402f1", None, None),
    FileSpec("lab_hours_inactive_target.py", 0o644,
             "f670077ec2be3001058c8a7f18b8da55e5f717422305c400afd97350bc7cefab", None, None),
    FileSpec("lab_hours_reservations.py", 0o755,
             "f61c6b496fd6e378b6e144a2b13170c85392274e86127a29b03d0cf8f16415d2",
             "f3f112c31c30776e94889d1a372b0584b9460007369fc7986a3c5f90e6c92322", 0o755),
    FileSpec("lab_hours_reserved_runner.py", 0o755,
             "79b3fb92ced17712f7f5dd8bd40517fbec27ef2b2494c47454fb8fdcd44bf27e",
             "6ba44c2bfb6322d68c5bd6c112e4144916be60f2ee4ae0abf2042e09a456abd2", 0o755),
    FileSpec("lab_hours_release_manifest.json", 0o644,
             "7aa4a8c1d04d0e208b0cc732931592c94a6e49e18e3a1bdaf52c1532d7ff2c14",
             "b2c61494d572e17f3f1d4c71564f1b8c8f43728d9063c8d39e0c49e637593bed", 0o644),
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, *, uid: int, mode: int | None = None) -> tuple[bytes, os.stat_result]:
    try:
        info = path.lstat()
    except FileNotFoundError as exc:
        raise RegistrationInstallError(f"TARGET_MISSING:{path.name}") from exc
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid or info.st_nlink != 1
            or (mode is not None and stat.S_IMODE(info.st_mode) != mode)):
        raise RegistrationInstallError(f"TARGET_CUSTODY_INVALID:{path.name}")
    return path.read_bytes(), info


def source_bytes(source_root: Path, spec: FileSpec, *, uid: int) -> bytes:
    path = source_root / "scripts/local-ai" / spec.name
    data, info = regular(path, uid=uid, mode=None)
    if stat.S_IMODE(info.st_mode) not in {0o644, 0o755} or digest(data) != spec.new_sha256:
        raise RegistrationInstallError(f"SOURCE_INVALID:{spec.name}")
    return data


def atomic(path: Path, data: bytes, *, uid: int, mode: int) -> None:
    parent = path.parent
    info = parent.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != uid:
        raise RegistrationInstallError("TARGET_ROOT_CUSTODY_INVALID")
    temporary = parent / f".{path.name}.sa3-registration-{os.getpid()}"
    if os.path.lexists(temporary):
        raise RegistrationInstallError(f"TEMPORARY_EXISTS:{path.name}")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data)
        os.fchmod(descriptor, mode)
        if uid == 0:
            os.fchown(descriptor, 0, 0)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    directory = os.open(parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def preflight(target_root: Path, source_root: Path, *, uid: int) -> dict[str, bytes]:
    info = target_root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != uid:
        raise RegistrationInstallError("TARGET_ROOT_CUSTODY_INVALID")
    for unit in HOST_UNITS:
        if os.path.lexists(unit):
            raise RegistrationInstallError(f"UNIT_MUST_BE_ABSENT:{unit.name}")
    values = {spec.name: source_bytes(source_root, spec, uid=uid) for spec in FILES}
    for spec in FILES:
        target = target_root / spec.name
        if spec.old_sha256 is None:
            if os.path.lexists(target):
                raise RegistrationInstallError(f"NEW_TARGET_NOT_ABSENT:{spec.name}")
        else:
            data, _ = regular(target, uid=uid, mode=spec.old_mode)
            if digest(data) != spec.old_sha256:
                raise RegistrationInstallError(f"BASELINE_DRIFT:{spec.name}")
    manifest = json.loads(values["lab_hours_release_manifest.json"])
    pins = manifest.get("pins") if isinstance(manifest, dict) else None
    if not isinstance(pins, dict):
        raise RegistrationInstallError("MANIFEST_INVALID")
    planned = {spec.name: spec.new_sha256 for spec in FILES}
    for name, expected in pins.items():
        if planned.get(name) == expected:
            continue
        data, _ = regular(target_root / name, uid=uid, mode=None)
        if digest(data) != expected:
            raise RegistrationInstallError(f"MANIFEST_BASELINE_DRIFT:{name}")
    return values


def checkpoint(target_root: Path, checkpoint_root: Path, *, uid: int) -> None:
    if os.path.lexists(checkpoint_root):
        raise RegistrationInstallError("CHECKPOINT_ALREADY_EXISTS")
    checkpoint_root.mkdir(parents=True, mode=0o700)
    os.chmod(checkpoint_root, 0o700)
    if uid == 0:
        os.chown(checkpoint_root, 0, 0)
    rows = []
    for spec in FILES:
        path = target_root / spec.name
        if spec.old_sha256 is None:
            row = {"name": spec.name, "present": False}
        else:
            data, info = regular(path, uid=uid, mode=spec.old_mode)
            row = {"name": spec.name, "present": True, "mode": stat.S_IMODE(info.st_mode),
                   "sha256": digest(data), "data": base64.b64encode(data).decode()}
        payload = (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
        atomic(checkpoint_root / (hashlib.sha256(spec.name.encode()).hexdigest() + ".json"),
               payload, uid=uid, mode=0o600)
        rows.append(spec.name)
    atomic(checkpoint_root / "manifest.json",
           (json.dumps({"files": rows}, sort_keys=True) + "\n").encode(),
           uid=uid, mode=0o600)


def rollback(target_root: Path, checkpoint_root: Path, *, uid: int) -> None:
    for spec in reversed(FILES):
        record_path = checkpoint_root / (hashlib.sha256(spec.name.encode()).hexdigest() + ".json")
        raw, _ = regular(record_path, uid=uid, mode=0o600)
        record = json.loads(raw)
        target = target_root / spec.name
        if os.path.lexists(target):
            current, _ = regular(target, uid=uid, mode=None)
            if digest(current) not in {spec.new_sha256, spec.old_sha256}:
                raise RegistrationInstallError(f"ROLLBACK_UNCERTAIN:{spec.name}")
        if record["present"]:
            atomic(target, base64.b64decode(record["data"]), uid=uid, mode=int(record["mode"]))
        elif os.path.lexists(target):
            target.unlink()


def postcheck(target_root: Path, *, uid: int) -> None:
    for spec in FILES:
        data, _ = regular(target_root / spec.name, uid=uid, mode=spec.mode)
        if digest(data) != spec.new_sha256:
            raise RegistrationInstallError(f"POSTCHECK_FAILED:{spec.name}")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(target_root)
    result = subprocess.run((sys.executable, "-B", "-c",
        "import lab_hours_workloads, lab_hours_inactive_target, lab_hours_reservations, lab_hours_reserved_runner"),
        env=env, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RegistrationInstallError("TARGET_IMPORT_FAILED:" + result.stderr[-300:])


def install(source_root: Path, *, target_root: Path = TARGET_ROOT,
            checkpoint_root: Path = CHECKPOINT, uid: int = 0) -> dict[str, object]:
    values = preflight(target_root, source_root, uid=uid)
    checkpoint(target_root, checkpoint_root, uid=uid)
    try:
        for spec in FILES:
            atomic(target_root / spec.name, values[spec.name], uid=uid, mode=spec.mode)
        postcheck(target_root, uid=uid)
        return {"state": "installed-inactive", "files": len(FILES),
                "registration": "sa3-expanded-source-quality-v1",
                "effects": "not-attempted", "checkpoint": "retained"}
    except BaseException:
        rollback(target_root, checkpoint_root, uid=uid)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"}, sort_keys=True))
        return 2
    try:
        if os.geteuid() != 0:
            raise RegistrationInstallError("ROOT_REQUIRED")
        print(json.dumps(install(args.source_root), sort_keys=True))
        return 0
    except (RegistrationInstallError, OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
