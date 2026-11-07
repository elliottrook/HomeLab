"""Reversibly install the exact K2 sealed runtime bundle, inactive."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import tarfile

import m3_k2_sealed_bundle_contract as bundle_contract


class InstallError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def _absent(path: Path, label: str) -> None:
    if os.path.lexists(path):
        raise InstallError(label + "_EXISTS")


def _directory(path: Path, uid: int) -> None:
    info = path.lstat()
    if (not stat.S_ISDIR(info.st_mode) or path.is_symlink()
            or info.st_uid != uid or info.st_nlink < 1
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise InstallError("DIRECTORY_CUSTODY:" + path.name)


def _regular(path: Path, uid: int) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or path.is_symlink()
            or info.st_uid != uid or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) != 0o600):
        raise InstallError("FILE_CUSTODY:" + path.name)
    return path.read_bytes()


def _write(path: Path, raw: bytes, uid: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        os.write(descriptor, raw)
        os.fchmod(descriptor, 0o600)
        if os.geteuid() == 0:
            os.fchown(descriptor, uid, -1)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _members(raw: bytes) -> dict[str, bytes]:
    bundle_contract.validate(raw)
    expected = {"MANIFEST.json", *bundle_contract.SOURCE_PINS}
    values: dict[str, bytes] = {}
    try:
        archive = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
    except (tarfile.TarError, OSError) as exc:
        raise InstallError("BUNDLE_CONTAINER") from exc
    with archive:
        for member in archive.getmembers():
            name = member.name.removeprefix("runtime/")
            if name not in expected or name in values:
                raise InstallError("BUNDLE_MEMBER_SET")
            stream = archive.extractfile(member)
            if stream is None:
                raise InstallError("BUNDLE_MEMBER_READ")
            values[name] = stream.read(1_048_577)
    if set(values) != expected:
        raise InstallError("BUNDLE_MEMBER_SET")
    return values


def _marker(target: Path) -> dict[str, object]:
    return {
        "schema": "aster-m3-k2-sealed-runtime-inactive-checkpoint.v1",
        "target": str(target),
        "target_was_absent": True,
        "bundle_sha256": bundle_contract.BUNDLE_SHA256,
        "preregistration_sha256": bundle_contract.PREREGISTRATION_SHA256,
        "source_files": len(bundle_contract.SOURCE_PINS),
        "effect_authorized": False,
        "authority": "not-granted",
    }


def validate_installed(target: Path, raw: bytes, *, uid: int) -> dict[str, object]:
    members = _members(raw)
    _directory(target, uid)
    observed = {item.name for item in target.iterdir()}
    if observed != set(members):
        raise InstallError("INSTALLED_MEMBER_SET")
    for name, expected in members.items():
        if hashlib.sha256(_regular(target / name, uid)).digest() != hashlib.sha256(expected).digest():
            raise InstallError("INSTALLED_IDENTITY:" + name)
    return {"state": "installed-inactive", "files": len(members),
            "bundle_sha256": bundle_contract.BUNDLE_SHA256,
            "effect_authorized": False, "authority": "not-granted"}


def install(target: Path, checkpoint: Path, raw: bytes, *,
            expected_uid: int | None = None) -> dict[str, object]:
    uid = os.geteuid() if expected_uid is None else expected_uid
    members = _members(raw)
    stage = target.parent / ("." + target.name + ".installing")
    _absent(target, "TARGET")
    _absent(checkpoint, "CHECKPOINT")
    _absent(stage, "STAGE")
    checkpoint.mkdir(mode=0o700)
    os.chmod(checkpoint, 0o700)
    _directory(checkpoint, uid)
    _write(checkpoint / "target-was-absent.json", canonical(_marker(target)), uid)
    stage.mkdir(mode=0o700)
    os.chmod(stage, 0o700)
    try:
        _directory(stage, uid)
        for name, content in sorted(members.items()):
            _write(stage / name, content, uid)
        os.rename(stage, target)
        result = validate_installed(target, raw, uid=uid)
        result["checkpoint"] = "retained"
        result["service_restart"] = False
        result["workload_effect"] = "not-attempted"
        return result
    except BaseException:
        if os.path.lexists(stage):
            for name in members:
                item = stage / name
                if os.path.lexists(item):
                    item.unlink()
            stage.rmdir()
        raise


def rollback(target: Path, checkpoint: Path, raw: bytes, *,
             expected_uid: int | None = None) -> dict[str, object]:
    uid = os.geteuid() if expected_uid is None else expected_uid
    members = _members(raw)
    validate_installed(target, raw, uid=uid)
    _directory(checkpoint, uid)
    marker = _regular(checkpoint / "target-was-absent.json", uid)
    if marker != canonical(_marker(target)):
        raise InstallError("CHECKPOINT_IDENTITY")
    for name in sorted(members):
        (target / name).unlink()
    target.rmdir()
    if os.path.lexists(target):
        raise InstallError("ROLLBACK_UNCERTAIN")
    return {"state": "rolled-back", "target_absent": True,
            "checkpoint": "retained", "service_restart": False,
            "workload_effect": "not-attempted", "authority": "not-granted"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--checkpoint", required=True, type=Path)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--apply", action="store_true")
    operation.add_argument("--rollback", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply and not args.rollback:
        print(json.dumps({"state": "source-only", "reason":
                          "--apply or --rollback required"}, sort_keys=True))
        return 2
    try:
        raw = args.bundle.read_bytes()
        value = (install(args.target, args.checkpoint, raw) if args.apply
                 else rollback(args.target, args.checkpoint, raw))
        print(json.dumps(value, sort_keys=True, separators=(",", ":")))
        return 0
    except (InstallError, OSError, ValueError, tarfile.TarError) as exc:
        print(json.dumps({"state": "no_go", "failure_class":
                          type(exc).__name__, "authority": "not-granted"},
                         sort_keys=True, separators=(",", ":")))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
