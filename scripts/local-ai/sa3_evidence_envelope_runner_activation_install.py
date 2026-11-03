"""Atomic inactive activation of the candidate-g reserved-runner path."""

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
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-envelope-runner-activation-v1")
RESERVATIONS = Path("/var/lib/local-ai-lab/reservations")
STATE_ROOT = Path("/var/lib/local-ai-lab")
FILES = {
    "full_inference_lab_runtime.py": (
        "875836ce3347aacea1fddcc4f10976f864d5db27fdd930897cdde9f89e1aef40",
        "b4fc31b0eaeab14b0beb81b47103f2d03a62cf9e6bf3bbccdfc4560a0f444da9",
        0o755),
    "lab_hours_reserved_runner.py": (
        "ee4ab4c389e7c9cffd3cbcdd2ea7f7dbf882ccfc49312af04a3d52dd666f5abf",
        "63c7a116f326161dfb550cb3bfdaf268cbab29820e7b9f0105e810c595a75aba",
        0o755),
    "lab_hours_release_manifest.json": (
        "9dfea8ad72f330106384314f16f9798b2201f3ea1289f25dab3a1eb408196792",
        "c970bd70cc7e97fa707bdec50a027add4e6a3a77189aa5a86903be6e4b049886",
        0o644),
}


class ActivationError(RuntimeError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, expected: str, mode: int | None, uid: int) -> bytes:
    info = path.lstat()
    data = path.read_bytes()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != uid or info.st_nlink != 1
            or (mode is not None and stat.S_IMODE(info.st_mode) != mode)
            or sha(data) != expected):
        raise ActivationError("FILE_INVALID:" + path.name)
    return data


def atomic(path: Path, data: bytes, mode: int, uid: int) -> None:
    temporary = path.parent / ("." + path.name + ".envelope-activation-" + str(os.getpid()))
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


def require_quiet(reservations: Path, state_root: Path) -> None:
    for name in ("full-inference-drain.json", "full-inference-drain.lock",
                 "local-ai-lease.json", "local-ai-lease.lock"):
        if os.path.lexists(state_root / name):
            raise ActivationError("ACTIVE_STATE_PRESENT:" + name)
    if not reservations.exists():
        return
    for path in reservations.glob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        state = value.get("state")
        if (state in {"claimed", "running"}
                or (state == "reserved" and value.get("workload") is not None)):
            raise ActivationError("ACTIVE_BOOKING_PRESENT")


def install(source_root: Path, *, target: Path = TARGET, checkpoint: Path = CHECKPOINT,
            reservations: Path = RESERVATIONS, state_root: Path = STATE_ROOT,
            uid: int = 0, run=subprocess.run) -> dict[str, object]:
    if os.path.lexists(checkpoint):
        raise ActivationError("CHECKPOINT_EXISTS")
    require_quiet(reservations, state_root)
    old: dict[str, bytes] = {}
    new: dict[str, bytes] = {}
    for name, (before, after, mode) in FILES.items():
        old[name] = regular(target / name, before, mode, uid)
        new[name] = regular(source_root / "scripts/local-ai" / name, after, None, uid)
    checkpoint.mkdir(parents=True, mode=0o700)
    os.chmod(checkpoint, 0o700)
    if uid == 0:
        os.chown(checkpoint, 0, 0)
    for name, data in old.items():
        record = (json.dumps({"name": name, "data": base64.b64encode(data).decode()},
                             sort_keys=True) + "\n").encode()
        atomic(checkpoint / (hashlib.sha256(name.encode()).hexdigest() + ".json"),
               record, 0o600, uid)
    try:
        for name, (_, _, mode) in FILES.items():
            atomic(target / name, new[name], mode, uid)
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        environment["PYTHONPATH"] = str(target)
        result = run((sys.executable, "-B", "-c",
                      "import full_inference_lab_runtime,lab_hours_reserved_runner; "
                      "from lab_hours_reserved_runner import load_manifest; "
                      "assert 'sa3-evidence-envelope-quality' in "
                      "lab_hours_reserved_runner.REGISTERED_RUNNER_KINDS; load_manifest()"),
                     env=environment, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode != 0:
            raise ActivationError("IMPORT_OR_MANIFEST_FAILED:" + result.stderr[-240:])
        return {"state": "installed-inactive", "files": 3,
                "runner": "sa3-evidence-envelope-quality", "effects": "not-attempted",
                "checkpoint": "retained"}
    except BaseException:
        for name, (_, _, mode) in reversed(tuple(FILES.items())):
            record_path = checkpoint / (hashlib.sha256(name.encode()).hexdigest() + ".json")
            record = json.loads(record_path.read_text(encoding="utf-8"))
            atomic(target / name, base64.b64decode(record["data"]), mode, uid)
        raise


def main(argv: list[str] | None = None) -> int:
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
            raise ActivationError("ROOT_REQUIRED")
        print(json.dumps(install(args.source_root), sort_keys=True))
        return 0
    except (ActivationError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
