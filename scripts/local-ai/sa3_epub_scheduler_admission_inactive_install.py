"""Reversibly install the current EPUB scheduler admission and release pin."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import InstallError, atomic, digest, regular, source


HOST_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-epub-scheduler-admission-20261104")
FILES = {
    "full_inference_lab_sources.py": (
        "6103da31e85e957ae9491c2d64bd3f2bfb497c31db5c8bac0616786fff4c13ad",
        "9020fac1a35c897270ef14f9e4abf5ede649ccd98f7023dbdf26b5682a3e37c3"),
    "lab_hours_release_manifest.json": (
        "4d8e7db28b86d48a4af049c491143a9dfbf0c7638bfda52ceff30fff24db2b92",
        "76f84525ad80d79267d03598cf85465c2eba03693fe3e1486d7377831312ce64"),
}


def _quiet() -> None:
    for path in (Path("/var/lib/local-ai-lab/full-inference-drain.json"),
                 Path("/var/lib/local-ai-lab/full-inference-drain.lock"),
                 Path("/run/local-ai-lab-operation.lock")):
        if path.exists():
            raise InstallError("SHARED_STATE_OR_LOCK_PRESENT")
    status = subprocess.run(("/usr/local/sbin/local-ai-lease", "status"),
                            capture_output=True, text=True, timeout=10, check=False)
    try:
        value = json.loads(status.stdout)
    except json.JSONDecodeError:
        value = None
    if status.returncode or value not in ("ready", {"state": "ready"}):
        raise InstallError("LEASE_NOT_READY")


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    _quiet()
    data = {}
    for name, (old, new) in FILES.items():
        if digest(regular(HOST_ROOT / name, 0o644)) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        data[name] = source(stage, "scripts/local-ai/" + name, new)
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name in FILES:
        atomic(CHECKPOINT / name, regular(HOST_ROOT / name, 0o644), 0o600)
    try:
        for name in FILES:
            atomic(HOST_ROOT / name, data[name], 0o644)
        for name, (_, expected) in FILES.items():
            if digest(regular(HOST_ROOT / name, 0o644)) != expected:
                raise InstallError("POSTCHECK:" + name)
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONPATH": str(HOST_ROOT)}
        expression = (
            "import subprocess; from full_inference_lab_sources import epub_narration_healthy; "
            "from lab_hours_reserved_runner import load_manifest; "
            "run=lambda c: subprocess.run(c,capture_output=True,text=True,timeout=10,check=False).stdout.strip(); "
            "assert epub_narration_healthy(run); print(len(load_manifest()))"
        )
        check = subprocess.run(("/usr/bin/python3", "-B", "-c", expression),
                               env=environment, capture_output=True, text=True,
                               timeout=60, check=False)
        if check.returncode or not check.stdout.strip().isdigit():
            raise InstallError("INSTALLED_ADMISSION_VALIDATION_FAILED")
        _quiet()
        return {"state": "installed-inactive", "files": 2,
                "checkpoint": "retained", "epub_scheduler_admitted": True,
                "manifest_pins_valid": True, "booking": "absent",
                "service_restart": False, "workload_effect": "not-attempted"}
    except BaseException:
        for name in reversed(tuple(FILES)):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), 0o644)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"},
                         sort_keys=True))
        return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True))
        return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
