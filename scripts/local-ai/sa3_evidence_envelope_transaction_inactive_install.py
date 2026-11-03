"""Reversible inactive installation of the candidate-g transaction closure."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import (
    GUEST_ROOT, HOST_ROOT, InstallError, atomic, digest, guest, regular, source,
)


CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-evidence-envelope-transaction-v2")
GUEST_CHECKPOINT = "/var/lib/local-ai-lab/checkpoints/sa3-evidence-envelope-transaction-v2"
UNIT_PREFIX = "aster-lab-hours-booking-sa3-evidence-envelope-quality-v1"
HOST_FILES = {
    "sa3_evidence_envelope_transaction.py": (
        None, "b906f30dd25a7990f3a81f6b41eeb77ab67e9b0aa96fffcdf56bee111ee3fa26", 0o644),
    "sa3_evidence_envelope_listener_adapter.py": (
        None, "e668c6caec4881e010584fb01ebeebcc1e935ba3a00817c94bd814553c4123ae", 0o644),
    "lab_hours_release_manifest.json": (
        "36e2024248e1c64a9c3448db6b12efff3fcc1228dd867aba3ebf8248b9d0d84d",
        "9dfea8ad72f330106384314f16f9798b2201f3ea1289f25dab3a1eb408196792", 0o644),
}
GUEST_FILES = {
    "aster_llama_sa3_evidence_envelope_wrapper.py":
        "8e9e01ebf42c0b90a40e16f28e6e8155143118058ec5213edf52686f8c26a36f",
}


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    for suffix in (".service", ".timer"):
        if Path("/etc/systemd/system", UNIT_PREFIX + suffix).exists():
            raise InstallError("UNIT_PRESENT:" + suffix)
    host_data = {}
    for name, (old, new, mode) in HOST_FILES.items():
        target = HOST_ROOT / name
        if old is None:
            if os.path.lexists(target):
                raise InstallError("TARGET_PRESENT:" + name)
        elif digest(regular(target, mode)) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        host_data[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_data = {
        name: source(stage, "scripts/local-ai/" + name, expected)
        for name, expected in GUEST_FILES.items()
    }
    CHECKPOINT.mkdir(parents=True, mode=0o700); os.chmod(CHECKPOINT, 0o700)
    manifest = {}
    for name, (old, _, _) in HOST_FILES.items():
        if old is None:
            manifest[name] = {"present": False}
        else:
            data = regular(HOST_ROOT / name)
            atomic(CHECKPOINT / name, data, 0o600)
            manifest[name] = {"present": True, "sha256": digest(data)}
    atomic(CHECKPOINT / "manifest.json",
           (json.dumps(manifest, sort_keys=True) + "\n").encode(), 0o600)
    guest("preflight", {"root": GUEST_ROOT, "checkpoint": GUEST_CHECKPOINT,
                         "pins": GUEST_FILES})
    guest_started = False
    try:
        for name, (_, _, mode) in HOST_FILES.items():
            atomic(HOST_ROOT / name, host_data[name], mode)
        guest_started = True
        for name, expected in GUEST_FILES.items():
            guest("install", {"root": GUEST_ROOT, "name": name, "sha256": expected,
                              "data": base64.b64encode(guest_data[name]).decode()})
        guest_value = json.loads(guest("verify", {"root": GUEST_ROOT, "pins": GUEST_FILES}))
        for name, (_, new, mode) in HOST_FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != new:
                raise InstallError("POSTCHECK:" + name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(HOST_ROOT)}
        check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_reserved_runner as r, sa3_evidence_envelope_transaction, sa3_evidence_envelope_listener_adapter; r.load_manifest()"),
            env=env, capture_output=True, text=True, timeout=30, check=False)
        if check.returncode:
            raise InstallError("HOST_IMPORT_OR_MANIFEST:" + check.stderr[-240:])
        guest_import = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import aster_llama_sa3_evidence_envelope_wrapper"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_import.returncode:
            raise InstallError("GUEST_IMPORT:" + guest_import.stderr[-240:])
        return {"state": "installed-inactive", "host_files": len(HOST_FILES),
                "guest": guest_value, "effects": "not-attempted",
                "runner_activation": "absent", "checkpoint": "retained"}
    except BaseException:
        if guest_started:
            guest("rollback", {"root": GUEST_ROOT, "pins": GUEST_FILES})
        for name, (old, _, mode) in reversed(tuple(HOST_FILES.items())):
            target = HOST_ROOT / name
            if old is None:
                if os.path.lexists(target):
                    current = regular(target)
                    if digest(current) != HOST_FILES[name][1]:
                        raise InstallError("ROLLBACK_UNCERTAIN:" + name)
                    target.unlink()
            else:
                atomic(target, regular(CHECKPOINT / name, 0o600), mode)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--apply", action="store_true"); args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"}, sort_keys=True)); return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True)); return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
