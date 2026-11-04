"""Reversibly install the current EPUB scheduler admission and release pin."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import InstallError, atomic, digest, regular, source


HOST_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-epub-scheduler-path-r3-20261104")
FILES = {
    "full_inference_lab_session.py": (
        "217cd468111b5e3fea280515a9ac7b9e5b77776c5510764c8b9ca8803ddf5b02",
        "b3c38f030cbe1c0d45f59947cb2bc68cb7f80ed6410ef1669c88c18027296e9a", 0o644),
    "lab_hours_doctor.py": (
        "28999eb78f0f93c6b463944df5bb63251c014e47aa8bc697caccf53357580397",
        "32fbe1d9e63fdab78a00496c36ca4b3da7a81809e14cf930a209a32ec9649d76", 0o755),
    "lab_hours_release_manifest.json": (
        "d92f9b34c500310fd3427955a0dc53b5965400067edde36639312d1cc14266d0",
        "b29f1e6c6f0a57622dd81a6274076234db22b141fa75bbbaeecfc6f641f41987", 0o644),
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
    for name, (old, new, mode) in FILES.items():
        if digest(regular(HOST_ROOT / name, mode)) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        data[name] = source(stage, "scripts/local-ai/" + name, new)
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name in FILES:
        atomic(CHECKPOINT / name, regular(HOST_ROOT / name, 0o644), 0o600)
    try:
        for name in FILES:
            atomic(HOST_ROOT / name, data[name], FILES[name][2])
        for name, (_, expected, mode) in FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != expected:
                raise InstallError("POSTCHECK:" + name)
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                       "PYTHONPATH": str(HOST_ROOT)}
        expression = (
            "import subprocess; from full_inference_lab_sources import epub_narration_healthy; "
            "from lab_hours_reserved_runner import load_manifest; "
            "from lab_hours_doctor import diagnose, ReservationStore, RESERVATIONS; "
            "from full_inference_lab_session import canonical_commands; "
            "run=lambda c: subprocess.run(c,capture_output=True,text=True,timeout=10,check=False).stdout.strip(); "
            "assert epub_narration_healthy(run); "
            "assert diagnose(ReservationStore(RESERVATIONS))['state']=='healthy'; "
            "commands=canonical_commands(); "
            "assert 'epub-narration-worker.timer' not in repr(commands); "
            "print(len(load_manifest()))"
        )
        check = subprocess.run(("/usr/bin/python3", "-B", "-c", expression),
                               env=environment, capture_output=True, text=True,
                               timeout=60, check=False)
        if check.returncode or not check.stdout.strip().isdigit():
            raise InstallError("INSTALLED_ADMISSION_VALIDATION_FAILED")
        _quiet()
        return {"state": "installed-inactive", "files": 3,
                "checkpoint": "retained", "epub_scheduler_admitted": True,
                "manifest_pins_valid": True, "booking": "absent",
                "service_restart": False, "workload_effect": "not-attempted"}
    except BaseException:
        for name in reversed(tuple(FILES)):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), FILES[name][2])
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
