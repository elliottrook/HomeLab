"""Reversibly install the candidate-g bounded diagnostic correction inactive."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import (
    GUEST_ROOT, HOST_ROOT, InstallError, atomic, digest, regular, source,
)


CHECKPOINT = Path(
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-diagnostic-r1-20261104")
GUEST_CHECKPOINT = (
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-diagnostic-r1-20261104")
HOST_FILES = {
    "sa3_evidence_envelope_listener_adapter.py": (
        "e668c6caec4881e010584fb01ebeebcc1e935ba3a00817c94bd814553c4123ae",
        "fecb32cb29b2981aeab769efff7450e93c9853b30f79ca2131acb4015c74600c",
        0o644),
    "lab_hours_release_manifest.json": (
        "b29f1e6c6f0a57622dd81a6274076234db22b141fa75bbbaeecfc6f641f41987",
        "6fa56d9c98817e84875966fb5addb6006fa14e9f07edb4cf3acbebc50a157f71",
        0o644),
}
GUEST_FILES = {
    "aster_llama_sa3_evidence_envelope_wrapper.py": (
        "8e9e01ebf42c0b90a40e16f28e6e8155143118058ec5213edf52686f8c26a36f",
        "1d01c8c5bda942ddb42386eb56066c4858bf8032db39c136a4c9efbb933a4fc2",
        0o644),
}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1]; v=json.loads(sys.stdin.read()); root=Path(v["root"]); cp=Path(v["checkpoint"])
def regular(p,mode):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes()
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".candidate-g-diagnostic")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS:"+p.name)
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data); os.fchmod(fd,mode); os.fchown(fd,0,0); os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,p)
name=v["name"]; target=root/name; old=v["old"]; new=v["new"]; mode=v["mode"]
if op=="preflight":
 data=regular(target,mode)
 if hashlib.sha256(data).hexdigest()!=old: raise SystemExit("BASELINE_DRIFT:"+name)
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 cp.mkdir(parents=True,mode=0o700); os.chmod(cp,0o700); os.chown(cp,0,0)
 atomic(cp/name,data,0o600); print("{}")
elif op=="install":
 data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=new: raise SystemExit("SOURCE_HASH:"+name)
 if hashlib.sha256(regular(target,mode)).hexdigest()!=old: raise SystemExit("BASELINE_DRIFT:"+name)
 atomic(target,data,mode); print("{}")
elif op=="verify":
 if hashlib.sha256(regular(target,mode)).hexdigest()!=new: raise SystemExit("POSTCHECK:"+name)
 print(json.dumps({"state":"valid","sha256":new},sort_keys=True))
elif op=="rollback":
 if hashlib.sha256(regular(target,mode)).hexdigest()!=new: raise SystemExit("ROLLBACK_UNCERTAIN:"+name)
 data=regular(cp/name,0o600)
 if hashlib.sha256(data).hexdigest()!=old: raise SystemExit("CHECKPOINT_DRIFT:"+name)
 atomic(target,data,mode); print("{}")
'''


def _quiet() -> None:
    for path in (Path("/var/lib/local-ai-lab/full-inference-drain.json"),
                 Path("/var/lib/local-ai-lab/full-inference-drain.lock"),
                 Path("/run/local-ai-lab-operation.lock")):
        if path.exists():
            raise InstallError("SHARED_STATE_OR_LOCK_PRESENT")
    status = subprocess.run(("/usr/local/sbin/local-ai-lease", "status"),
                            capture_output=True, text=True, timeout=10,
                            check=False)
    try:
        value = json.loads(status.stdout)
    except json.JSONDecodeError:
        value = None
    if status.returncode or value not in ("ready", {"state": "ready"}):
        raise InstallError("LEASE_NOT_READY")


def _guest(op: str, name: str, data: bytes | None = None) -> str:
    old, new, mode = GUEST_FILES[name]
    value = {"root": GUEST_ROOT, "checkpoint": GUEST_CHECKPOINT,
             "name": name, "old": old, "new": new, "mode": mode}
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
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    _quiet()
    host_data = {}
    for name, (old, new, mode) in HOST_FILES.items():
        current = regular(HOST_ROOT / name, mode)
        if digest(current) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        host_data[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_data = {name: source(stage, "scripts/local-ai/" + name, new)
                  for name, (_, new, _) in GUEST_FILES.items()}
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, mode) in HOST_FILES.items():
        current = regular(HOST_ROOT / name, mode)
        atomic(CHECKPOINT / name, current, 0o600)
        if digest(current) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    guest_name = next(iter(GUEST_FILES))
    _guest("preflight", guest_name)
    guest_installed = False
    try:
        for name, (_, _, mode) in HOST_FILES.items():
            atomic(HOST_ROOT / name, host_data[name], mode)
        _guest("install", guest_name, guest_data[guest_name])
        guest_installed = True
        guest_value = json.loads(_guest("verify", guest_name))
        for name, (_, expected, mode) in HOST_FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != expected:
                raise InstallError("POSTCHECK:" + name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(HOST_ROOT)}
        host_check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_reserved_runner as r; "
            "import sa3_evidence_envelope_listener_adapter as a; "
            "assert a.bounded_guest_failure(b'noise\\n{\"code\":\"bounded\"}\\n')=='bounded'; "
            "assert len(r.load_manifest())==34"), env=env, capture_output=True,
            text=True, timeout=30, check=False)
        if host_check.returncode:
            raise InstallError("HOST_INSTALLED_PROOF:" + host_check.stderr[-240:])
        guest_check = subprocess.run(("pct", "exec", "110", "--",
            "/usr/bin/env", "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import unittest; import aster_llama_sa3_evidence_envelope_wrapper as w; "
            "unittest.TestCase().assertRaisesRegex(w.GuestError,'count=1;classes=TimeoutError',w.validate_result,{'errors':[{'error_class':'TimeoutError'}]})"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_check.returncode:
            raise InstallError("GUEST_INSTALLED_PROOF:" + guest_check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive", "host_files": 2,
                "guest": guest_value, "checkpoint": "retained",
                "booking": "absent", "service_restart": False,
                "workload_effect": "not-attempted"}
    except BaseException:
        if guest_installed:
            _guest("rollback", guest_name)
        for name in reversed(tuple(HOST_FILES)):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600),
                   HOST_FILES[name][2])
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
