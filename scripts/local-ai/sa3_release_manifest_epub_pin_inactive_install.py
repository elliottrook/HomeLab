"""Reversible inactive install of corrected SA3 release-manifest pins."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import InstallError, atomic, digest, regular, source


HOST_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
TARGET = HOST_ROOT / "lab_hours_release_manifest.json"
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-release-manifest-epub-pin-20261104")
OLD_SHA256 = "c970bd70cc7e97fa707bdec50a027add4e6a3a77189aa5a86903be6e4b049886"
NEW_SHA256 = "4d8e7db28b86d48a4af049c491143a9dfbf0c7638bfda52ceff30fff24db2b92"


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
    if digest(regular(TARGET, 0o644)) != OLD_SHA256:
        raise InstallError("BASELINE_DRIFT")
    candidate = source(stage, "scripts/local-ai/lab_hours_release_manifest.json", NEW_SHA256)
    CHECKPOINT.mkdir(parents=True, mode=0o700); os.chmod(CHECKPOINT, 0o700)
    atomic(CHECKPOINT / TARGET.name, regular(TARGET, 0o644), 0o600)
    try:
        atomic(TARGET, candidate, 0o644)
        if digest(regular(TARGET, 0o644)) != NEW_SHA256:
            raise InstallError("POSTCHECK")
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(HOST_ROOT)}
        check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "from lab_hours_reserved_runner import load_manifest; print(len(load_manifest()))"),
            env=environment, capture_output=True, text=True, timeout=60, check=False)
        if check.returncode or not check.stdout.strip().isdigit():
            raise InstallError("INSTALLED_MANIFEST_VALIDATION_FAILED")
        _quiet()
        return {"state": "installed-inactive", "files": 1,
                "checkpoint": "retained", "manifest_pins_valid": True,
                "booking": "absent", "service_restart": False,
                "workload_effect": "not-attempted"}
    except BaseException:
        atomic(TARGET, regular(CHECKPOINT / TARGET.name, 0o600), 0o644)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"}, sort_keys=True))
        return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True))
        return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
