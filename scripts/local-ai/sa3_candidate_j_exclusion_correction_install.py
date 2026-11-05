"""Replace only candidate-j's overbroad exclusion check and release manifest."""
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
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-j-exclusion-r1-20261104")
GUEST_CHECKPOINT = str(CHECKPOINT)
UNIT_PREFIX = "aster-lab-hours-booking-sa3-evidence-matrix-candidate-j-public-v1"
WRAPPER = "aster_llama_sa3_candidate_j_evidence_matrix_wrapper.py"
MANIFEST = "lab_hours_release_manifest.json"
OLD_WRAPPER = "ec6e2297665f169eb50c67be42aba592066fd0be1c9e14784ebd530e4921d2f8"
NEW_WRAPPER = "a883c144ead962dc5862c54005a90157db173e88667122a89a23496796f05f2a"
OLD_MANIFEST = "3c12af56e18612c314fdcc4cc336064264d1593a74bc94e9980357ab5366d9e8"
NEW_MANIFEST = "9eddfdd24ab10fb0b678479dabeae0ac6676997361d80f354bb7a7586e82d665"

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1];v=json.loads(sys.stdin.read());p=Path(v["path"]);cp=Path(v["checkpoint"])/v["name"]
def regular(x):
 s=x.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=0o644: raise SystemExit("CUSTODY")
 return x.read_bytes()
def atomic(x,data):
 t=x.parent/("."+x.name+".exclusion-fix")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS")
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data);os.fchmod(fd,0o644);os.fchown(fd,0,0);os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,x)
if op=="preflight":
 if hashlib.sha256(regular(p)).hexdigest()!=v["old"]: raise SystemExit("BASELINE_DRIFT")
 Path(v["checkpoint"]).mkdir(parents=True,mode=0o700);os.chmod(Path(v["checkpoint"]),0o700);os.chown(Path(v["checkpoint"]),0,0)
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 fd=os.open(cp,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,regular(p));os.fchown(fd,0,0);os.fsync(fd)
 finally: os.close(fd)
 print("{}")
elif op=="install":
 data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=v["new"]: raise SystemExit("SOURCE_HASH")
 if hashlib.sha256(regular(p)).hexdigest()!=v["old"]: raise SystemExit("BASELINE_DRIFT")
 atomic(p,data);print("{}")
elif op=="verify":
 if hashlib.sha256(regular(p)).hexdigest()!=v["new"]: raise SystemExit("POSTCHECK")
 print("{}")
elif op=="rollback":
 if hashlib.sha256(regular(p)).hexdigest()!=v["new"]: raise SystemExit("ROLLBACK_UNCERTAIN")
 data=cp.read_bytes()
 if hashlib.sha256(data).hexdigest()!=v["old"]: raise SystemExit("CHECKPOINT_DRIFT")
 atomic(p,data);print("{}")
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


def _guest(op: str, data: bytes | None = None) -> None:
    value = {"path": GUEST_ROOT + "/" + WRAPPER,
             "checkpoint": GUEST_CHECKPOINT, "name": WRAPPER,
             "old": OLD_WRAPPER, "new": NEW_WRAPPER}
    if data is not None:
        value["data"] = base64.b64encode(data).decode()
    result = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/python3",
                             "-B", "-c", REMOTE, op), input=json.dumps(value),
                            capture_output=True, text=True, timeout=30,
                            check=False)
    if result.returncode:
        raise InstallError("GUEST_" + op.upper() + ":"
                           + (result.stderr or result.stdout).strip()[-160:])


def install(stage: Path) -> dict[str, object]:
    if os.geteuid() != 0:
        raise InstallError("ROOT_REQUIRED")
    if CHECKPOINT.exists():
        raise InstallError("CHECKPOINT_EXISTS")
    for suffix in (".service", ".timer"):
        if Path("/etc/systemd/system", UNIT_PREFIX + suffix).exists():
            raise InstallError("UNIT_PRESENT:" + suffix)
    _quiet()
    targets = {
        WRAPPER: (OLD_WRAPPER, NEW_WRAPPER),
        MANIFEST: (OLD_MANIFEST, NEW_MANIFEST),
    }
    replacement = {}
    for name, (old, new) in targets.items():
        if digest(regular(HOST_ROOT / name, 0o644)) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        replacement[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_data = source(stage, "scripts/local-ai/" + WRAPPER, NEW_WRAPPER)
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, (old, _) in targets.items():
        data = regular(HOST_ROOT / name, 0o644)
        atomic(CHECKPOINT / name, data, 0o600)
        if digest(data) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    _guest("preflight")
    guest_started = False
    try:
        for name in (WRAPPER, MANIFEST):
            atomic(HOST_ROOT / name, replacement[name], 0o644)
        guest_started = True
        _guest("install", guest_data)
        _guest("verify")
        for name, (_, new) in targets.items():
            if digest(regular(HOST_ROOT / name, 0o644)) != new:
                raise InstallError("POSTCHECK:" + name)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
               "PYTHONPATH": str(HOST_ROOT)}
        check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_reserved_runner as r;"
            "import aster_llama_sa3_candidate_j_evidence_matrix_wrapper as w;"
            "assert len(r.load_manifest())==39;"
            "assert 'sa3-evidence-envelope-quality-v1.json' not in w.EXCLUDED;"
            "assert 'sa3-evidence-envelope-candidate-i-quality-v1.json' not in w.EXCLUDED"),
            env=env, capture_output=True, text=True, timeout=30, check=False)
        if check.returncode:
            raise InstallError("HOST_PROOF:" + check.stderr[-160:])
        guest = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import aster_llama_sa3_candidate_j_evidence_matrix_wrapper as w;"
            "assert 'sa3-evidence-envelope-quality-v1.json' not in w.EXCLUDED;"
            "assert 'sa3-evidence-envelope-candidate-i-quality-v1.json' not in w.EXCLUDED"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest.returncode:
            raise InstallError("GUEST_PROOF:" + guest.stderr[-160:])
        _quiet()
        return {"state": "installed-inactive", "host_replaced": 2,
                "guest_replaced": 1, "checkpoint": "retained",
                "service_restart": False, "workload_effect": "not-attempted",
                "booking": "absent"}
    except BaseException:
        if guest_started:
            _guest("rollback")
        for name, (_, new) in reversed(tuple(targets.items())):
            target = HOST_ROOT / name
            if digest(regular(target, 0o644)) != new:
                raise InstallError("ROLLBACK_UNCERTAIN:" + name)
            atomic(target, regular(CHECKPOINT / name, 0o600), 0o644)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
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
