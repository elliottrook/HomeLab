"""Reversible inactive install of the SA3 EPUB admission correction."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import InstallError, atomic, digest, regular, source


HOST_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-epub-admission-20261103")
FILES = {
    "full_inference_lab_sources.py": (
        "920d2ed171d314a6cb346032651c24a7972e51b2a91c2bb2892dcd9419c50d48",
        "6103da31e85e957ae9491c2d64bd3f2bfb497c31db5c8bac0616786fff4c13ad"),
    "full_inference_lab_validator.py": (
        "0c4a21d7894dd2c41d89aa00d2fa5969277991ff86febf8a89a61ac299966858",
        "094d588b5ff1a6cea1f102375930424ed389cc7af6750a941ce44363043bbf31"),
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
    CHECKPOINT.mkdir(parents=True, mode=0o700); os.chmod(CHECKPOINT, 0o700)
    for name in FILES:
        atomic(CHECKPOINT / name, regular(HOST_ROOT / name, 0o644), 0o600)
    try:
        for name in FILES:
            atomic(HOST_ROOT / name, data[name], 0o644)
        for name, (_, expected) in FILES.items():
            if digest(regular(HOST_ROOT / name, 0o644)) != expected:
                raise InstallError("POSTCHECK:" + name)
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(HOST_ROOT)}
        check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import full_inference_lab_sources, full_inference_lab_validator"),
            env=environment, capture_output=True, text=True, timeout=30, check=False)
        if check.returncode:
            raise InstallError("IMPORT_FAILED")
        _quiet()
        return {"state": "installed-inactive", "files": 2,
                "checkpoint": "retained", "effects": "not-attempted",
                "service_restart": False, "booking": "absent"}
    except BaseException:
        for name in reversed(tuple(FILES)):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), 0o644)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--apply", action="store_true"); args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"}, sort_keys=True)); return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True)); return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
