"""Reversibly install candidate-g explicit Python guest launch inactive."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import (
    HOST_ROOT, InstallError, atomic, digest, regular, source,
)
from sa3_candidate_g_diagnostic_inactive_install import _quiet


CHECKPOINT = Path(
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-explicit-python-r1-20261104")
FILES = {
    "sa3_evidence_envelope_listener_adapter.py": (
        "101ce58e6e103db22b9da9532528e44ac84171e178a5baeee0a4e196fe3e3c9f",
        "e8c8cbcc875fe3f48035425f776a59f5ab81a6564f3f6acba38eb1dd63597a1b",
        0o644),
    "lab_hours_release_manifest.json": (
        "1d18a86d756e6388a72794f74f3299611234be43937c12c32159f976556d9537",
        "7bbfd20888675768d544420e2d0a4f06e5c291f5c243c2e5dec3b2aa5d5596f0",
        0o644),
}


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    _quiet()
    data = {}
    for name, (old, new, mode) in FILES.items():
        current = regular(HOST_ROOT / name, mode)
        if digest(current) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        data[name] = source(stage, "scripts/local-ai/" + name, new)
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, mode) in FILES.items():
        current = regular(HOST_ROOT / name, mode)
        atomic(CHECKPOINT / name, current, 0o600)
        if digest(current) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    try:
        for name, (_, _, mode) in FILES.items():
            atomic(HOST_ROOT / name, data[name], mode)
        for name, (_, expected, mode) in FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != expected:
                raise InstallError("POSTCHECK:" + name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(HOST_ROOT)}
        proof = (
            "import lab_hours_reserved_runner as r; "
            "import sa3_evidence_envelope_listener_adapter as a; "
            "assert len(r.load_manifest())==34; "
            "c=a.listener_command(lease_id='lease-proof',generation=1); "
            "assert c[:4]==('pct','exec','110','--'); "
            "assert c[4:7]==('/usr/bin/python3','-B',a.LISTENER)")
        check = subprocess.run(("/usr/bin/python3", "-B", "-c", proof), env=env,
                               capture_output=True, text=True, timeout=30,
                               check=False)
        if check.returncode:
            raise InstallError("INSTALLED_COMMAND_PROOF:" + check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive", "files": 2,
                "checkpoint": "retained", "manifest_pins": 34,
                "booking": "absent", "service_restart": False,
                "workload_effect": "not-attempted"}
    except BaseException:
        for name in reversed(tuple(FILES)):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600),
                   FILES[name][2])
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
