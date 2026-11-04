"""Reversibly install the candidate-g class-only exception diagnostic."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import InstallError, source
from sa3_candidate_g_diagnostic_inactive_install import (
    GUEST_ROOT, REMOTE, _quiet,
)


CHECKPOINT = "/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-exception-class-r1-20261104"
NAME = "aster_llama_sa3_evidence_envelope_wrapper.py"
OLD = "1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2"
NEW = "626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe"
MODE = 0o644


def _guest(op: str, data: bytes | None = None) -> str:
    value = {"root": GUEST_ROOT, "checkpoint": CHECKPOINT, "name": NAME,
             "old": OLD, "new": NEW, "mode": MODE}
    if data is not None:
        value["data"] = base64.b64encode(data).decode()
    result = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/python3",
                             "-B", "-c", REMOTE, op), input=json.dumps(value),
                            capture_output=True, text=True, timeout=30,
                            check=False)
    if result.returncode:
        detail = (result.stderr or result.stdout).strip()[-240:]
        raise InstallError("GUEST_" + op.upper() + ":" + detail)
    return result.stdout.strip()


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    _quiet()
    data = source(stage, "scripts/local-ai/" + NAME, NEW)
    _guest("preflight")
    installed = False
    try:
        _guest("install", data)
        installed = True
        value = json.loads(_guest("verify"))
        proof = """import contextlib,io,json
from unittest.mock import patch
import aster_llama_sa3_evidence_envelope_wrapper as w
out=io.StringIO()
args=['--profile',w.PROFILE,'--port',str(w.PORT),'--requests',str(w.CASES),'--per-request-timeout',str(w.PER_REQUEST_TIMEOUT),'--deadline',str(w.DEADLINE),'--lease-id','lease-1','--generation','1','--scope-unit','fixed-scope']
with patch.object(w,'run',side_effect=KeyError('private-value')),contextlib.redirect_stderr(out):
 assert w.main(args)==1
value=json.loads(out.getvalue())
assert value['code']=='candidate-g guest exception-class:KeyError'
assert 'private-value' not in out.getvalue()
"""
        result = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c", proof), capture_output=True,
            text=True, timeout=30, check=False)
        if result.returncode:
            raise InstallError("GUEST_INSTALLED_PROOF:" + result.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive", "guest": value,
                "checkpoint": "retained", "booking": "absent",
                "service_restart": False, "workload_effect": "not-attempted"}
    except BaseException:
        if installed:
            _guest("rollback")
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
