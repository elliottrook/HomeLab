"""Reversibly install candidate-i's exact scope-name correction inactive."""
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
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-i-scope-r1-20261104")
FILES = {
    "sa3_candidate_i_evidence_envelope_listener_adapter.py": (
        "e16a251225ca0cc757c74cd3b38641700aeabf9f32391836309ebfe42fd0a8c6",
        "80e7491b3d9bd3c457bf362baae97ba3377ac260dde1169933ddbdbc97cc1ee6",
        0o644),
    "lab_hours_release_manifest.json": (
        "c2812b754c2d5c87156898548d63a407f5afcca7ac7d4000ece645b14a922a5e",
        "05e41525f08f52597128b6523b92c1ed7de3316cee09e3e79f95d347d31eb65d",
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
            "import sa3_candidate_i_evidence_envelope_listener_adapter as a; "
            "assert len(r.load_manifest())==36; "
            "scope=a.candidate_i_scope_unit('lease-1',2); "
            "assert scope.startswith('aster-llama-sa3-i-'); "
            "command=a.listener_command(lease_id='lease-1',generation=2); "
            "assert command[command.index('--scope-unit')+1]==scope")
        check = subprocess.run(("/usr/bin/python3", "-B", "-c", proof),
                               env=env, capture_output=True, text=True,
                               timeout=30, check=False)
        if check.returncode:
            raise InstallError("INSTALLED_SCOPE_PROOF:" + check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive", "files": 2,
                "checkpoint": "retained", "manifest_pins": 36,
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
