"""Reversible upgrade of the inactive SA3 host-to-LXC110 validator."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


TARGET = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-guest-validator-v1")
FILES = {
    "lab_hours_inactive_target.py": (
        "f670077ec2be3001058c8a7f18b8da55e5f717422305c400afd97350bc7cefab",
        "fd467544649cc877ca06f831d8f84aaca495416c19072256bd228fc11601ae33", 0o644),
    "lab_hours_release_manifest.json": (
        "7aa4a8c1d04d0e208b0cc732931592c94a6e49e18e3a1bdaf52c1532d7ff2c14",
        "51a9cd3a450710ad755cf924aef0df6e900edcf6cca2db4cffe054cb2437f74c", 0o644),
}


class UpgradeError(RuntimeError): pass


def digest(data: bytes) -> str: return hashlib.sha256(data).hexdigest()


def regular(path: Path, expected: str, mode: int, uid: int) -> bytes:
    s = path.lstat()
    data = path.read_bytes()
    if (not stat.S_ISREG(s.st_mode) or s.st_uid != uid or s.st_nlink != 1
            or stat.S_IMODE(s.st_mode) != mode or digest(data) != expected):
        raise UpgradeError("FILE_INVALID:" + path.name)
    return data


def atomic(path: Path, data: bytes, mode: int, uid: int) -> None:
    tmp = path.parent / ("." + path.name + ".sa3-validator-" + str(os.getpid()))
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, data); os.fchmod(fd, mode)
        if uid == 0: os.fchown(fd, 0, 0)
        os.fsync(fd)
    finally: os.close(fd)
    os.replace(tmp, path)


def install(source_root: Path, *, target: Path = TARGET,
            checkpoint: Path = CHECKPOINT, uid: int = 0,
            run=subprocess.run) -> dict[str, object]:
    if os.path.lexists(checkpoint): raise UpgradeError("CHECKPOINT_EXISTS")
    old = {}; new = {}
    for name, (old_hash, new_hash, mode) in FILES.items():
        old[name] = regular(target / name, old_hash, mode, uid)
        new[name] = regular(source_root / "scripts/local-ai" / name, new_hash, mode, uid)
    checkpoint.mkdir(parents=True, mode=0o700); os.chmod(checkpoint, 0o700)
    if uid == 0: os.chown(checkpoint, 0, 0)
    for name, data in old.items():
        payload = json.dumps({"name": name, "data": base64.b64encode(data).decode()},
                             sort_keys=True).encode() + b"\n"
        atomic(checkpoint / (hashlib.sha256(name.encode()).hexdigest()+".json"), payload, 0o600, uid)
    try:
        for name, (_, _, mode) in FILES.items(): atomic(target/name, new[name], mode, uid)
        env = os.environ.copy(); env["PYTHONDONTWRITEBYTECODE"] = "1"; env["PYTHONPATH"] = str(target)
        imported = run((sys.executable, "-B", "-c", "import lab_hours_inactive_target; from lab_hours_reserved_runner import load_manifest; load_manifest()"),
                       env=env, capture_output=True, text=True, timeout=30, check=False)
        if imported.returncode != 0: raise UpgradeError("IMPORT_OR_MANIFEST_FAILED:" + imported.stderr[-240:])
        validated = run((sys.executable, "-B", str(target/"lab_hours_inactive_target.py")),
                        env=env, capture_output=True, text=True, timeout=30, check=False)
        if validated.returncode != 0: raise UpgradeError("GUEST_VALIDATION_FAILED:" + (validated.stderr or validated.stdout)[-240:])
        value = json.loads(validated.stdout)
        if value.get("state") != "valid" or value.get("guest") != "110" or value.get("runtime_files") != 4:
            raise UpgradeError("GUEST_VALIDATION_RESULT_INVALID")
        return {"state":"installed-inactive","files":2,"guest_validation":"pass",
                "effects":"not-attempted","checkpoint":"retained"}
    except BaseException:
        for name, (_, _, mode) in reversed(tuple(FILES.items())):
            record = checkpoint / (hashlib.sha256(name.encode()).hexdigest()+".json")
            data = base64.b64decode(json.loads(record.read_text())["data"])
            atomic(target/name, data, mode, uid)
        raise


def main(argv=None) -> int:
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--source-root",type=Path,required=True); p.add_argument("--apply",action="store_true")
    a=p.parse_args(argv)
    if not a.apply:
        print(json.dumps({"state":"source-only","reason":"--apply required"},sort_keys=True)); return 2
    try:
        if os.geteuid()!=0: raise UpgradeError("ROOT_REQUIRED")
        print(json.dumps(install(a.source_root),sort_keys=True)); return 0
    except (UpgradeError,OSError,ValueError,subprocess.SubprocessError) as exc:
        print(json.dumps({"state":"no_go","code":str(exc)},sort_keys=True)); return 1


if __name__ == "__main__": raise SystemExit(main())
