"""Reversibly install Candidate-J quality inactive without a booking."""
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
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-j-quality-r1-20261105")
GUEST_CHECKPOINT = str(CHECKPOINT)
UNIT_PREFIX = "aster-lab-hours-booking-sa3-evidence-matrix-candidate-j-quality-v1"
HOST_REPLACE = {
    "lab_hours_workloads.py": (
        "10e1e8aad89f4910bd3eb139720abfabba87a7ef692522dea7ba9bad2ab18587",
        "a6a6acb58de8ca8fee2246522aa8e2aa3ebb7d57db2348d694238e4cffbcdfec", 0o755),
    "lab_hours_reserved_runner.py": (
        "eb06b9f54d10d622dee753a9e94e514c9fde2f7974ebc99d6c74e0f7a6179c7d",
        "4d28ccc44db8a343aa0a1e4baea87d4964bced7db53154f627b5904f7270b11b", 0o755),
    "full_inference_lab_runtime.py": (
        "c2dbe8f0a5a4f1ed7383db663875c4a7ab6cf6480df006bf671034f52ba1f484",
        "cddae0e3da7ad3c6c6b11b5fb2503f54dec916815e3eb336e13bed74c16b2f61", 0o755),
    "lab_hours_release_manifest.json": (
        "a78cc536df95d0c1c5356d974e9d1a076b8d4d7362895d008952fa939bd86e8e",
        "908b4fe5cd39fca781305913b426e8f6de5991e9246ba4ac16cab15ad9f2f64e", 0o600),
}
HOST_ADD = {
    "sa3_candidate_j_quality_transaction.py":
        ("81ef7c4c41262ed0fb53ae46b10db05892bc7cf8fb39e732eb905ab86f46de46", 0o644),
    "sa3_candidate_j_quality_listener_adapter.py":
        ("f69d67963cbceffdd467708e91a4cbb4fa2f74386b86f8c0f57767fe2ab9f66c", 0o644),
    "aster_llama_sa3_candidate_j_quality_wrapper.py":
        ("4d90550af1f5e62cc65dffb49f0724feb028b9e9fa8fdf3c58217c5881a1ba82", 0o644),
}
GUEST_EXISTING: dict[str, str] = {}
GUEST_ADD = {
    "sa3-evidence-matrix-candidate-j-quality-v1.json":
        "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132",
    "sa3_evidence_matrix_candidate_j_contract.py":
        "b243d429218b134177f2b2cdf5ca4e3f28c8e0ed08a55b11e9d2ccb6bd17b2af",
    "sa3_evidence_matrix_candidate_j_runner.py":
        "ee3410dbed70dc9399a094e0260e0af94985daef961017de2dd9f70b4691d223",
    "sa3_evidence_matrix_candidate_j_quality_runtime.py":
        "4ea9b457d605926d88ce3bce92de0e377d657a0737854df30fe23b182037fea4",
    "aster_llama_sa3_candidate_j_quality_wrapper.py":
        "4d90550af1f5e62cc65dffb49f0724feb028b9e9fa8fdf3c58217c5881a1ba82",
}
GUEST_SOURCE_PATHS = {
    "aster_llama_sa3_candidate_j_quality_wrapper.py":
        "scripts/local-ai/aster_llama_sa3_candidate_j_quality_wrapper.py",
    **{name: "services/aster-agent/evals/" + name
       for name in GUEST_ADD
       if name != "aster_llama_sa3_candidate_j_quality_wrapper.py"},
}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1];v=json.loads(sys.stdin.read());root=Path(v["root"]);cp=Path(v["checkpoint"])
def regular(p,mode):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes()
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".candidate-j")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS:"+p.name)
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data);os.fchmod(fd,mode);os.fchown(fd,0,0);os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,p)
if op=="preflight":
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 for n,h in v["existing"].items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=h: raise SystemExit("BASELINE_DRIFT:"+n)
 for n in v["add"]:
  if os.path.lexists(root/n): raise SystemExit("TARGET_PRESENT:"+n)
 cp.mkdir(parents=True,mode=0o700);os.chmod(cp,0o700);os.chown(cp,0,0)
 atomic(cp/"guest-manifest.json",(json.dumps({"absent":sorted(v["add"]),"existing":v["existing"]},sort_keys=True)+"\n").encode(),0o600);print("{}")
elif op=="install":
 n=v["name"];data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=v["add"][n]: raise SystemExit("SOURCE_HASH:"+n)
 if os.path.lexists(root/n): raise SystemExit("TARGET_PRESENT:"+n)
 atomic(root/n,data,0o644);print("{}")
elif op=="verify":
 for n,h in v["existing"].items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=h: raise SystemExit("EXISTING_DRIFT:"+n)
 for n,h in v["add"].items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=h: raise SystemExit("POSTCHECK:"+n)
 print(json.dumps({"added":len(v["add"]),"existing":len(v["existing"]),"state":"valid"},sort_keys=True))
elif op=="rollback":
 for n,h in v["add"].items():
  p=root/n
  if os.path.lexists(p):
   if hashlib.sha256(regular(p,0o644)).hexdigest()!=h: raise SystemExit("ROLLBACK_UNCERTAIN:"+n)
   p.unlink()
 print("{}")
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


def _guest(op: str, *, name: str | None = None,
           data: bytes | None = None) -> str:
    value = {"root": GUEST_ROOT, "checkpoint": GUEST_CHECKPOINT,
             "existing": GUEST_EXISTING, "add": GUEST_ADD}
    if name is not None:
        value["name"] = name
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
    for suffix in (".service", ".timer"):
        if Path("/etc/systemd/system", UNIT_PREFIX + suffix).exists():
            raise InstallError("UNIT_PRESENT:" + suffix)
    _quiet()
    replace_data = {}
    for name, (old, new, mode) in HOST_REPLACE.items():
        current = regular(HOST_ROOT / name, mode)
        if digest(current) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        replace_data[name] = source(stage, "scripts/local-ai/" + name, new)
    add_data = {}
    for name, (new, _) in HOST_ADD.items():
        if os.path.lexists(HOST_ROOT / name):
            raise InstallError("TARGET_PRESENT:" + name)
        add_data[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_data = {name: source(stage, GUEST_SOURCE_PATHS[name], expected)
                  for name, expected in GUEST_ADD.items()}
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, mode) in HOST_REPLACE.items():
        data = regular(HOST_ROOT / name, mode)
        atomic(CHECKPOINT / name, data, 0o600)
        if digest(data) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    atomic(CHECKPOINT / "host-manifest.json",
           (json.dumps({"absent": sorted(HOST_ADD),
                        "replaced": sorted(HOST_REPLACE)}, sort_keys=True)
            + "\n").encode(), 0o600)
    _guest("preflight")
    guest_started = False
    try:
        for name, (_, _, mode) in HOST_REPLACE.items():
            atomic(HOST_ROOT / name, replace_data[name], mode)
        for name, (_, mode) in HOST_ADD.items():
            atomic(HOST_ROOT / name, add_data[name], mode)
        guest_started = True
        for name in GUEST_ADD:
            _guest("install", name=name, data=guest_data[name])
        guest_value = json.loads(_guest("verify"))
        for name, (_, new, mode) in HOST_REPLACE.items():
            if digest(regular(HOST_ROOT / name, mode)) != new:
                raise InstallError("POSTCHECK:" + name)
        for name, (new, mode) in HOST_ADD.items():
            if digest(regular(HOST_ROOT / name, mode)) != new:
                raise InstallError("POSTCHECK:" + name)
        host_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(HOST_ROOT)}
        host_check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_reserved_runner as r,lab_hours_workloads as w;"
            "import full_inference_lab_runtime;"
            "import sa3_candidate_j_quality_transaction;"
            "import sa3_candidate_j_quality_listener_adapter;"
            "assert len(r.load_manifest())==46;"
            "s=w.workload('sa3-evidence-matrix-candidate-j-quality-v1');"
            "assert s.runner_kind in r.REGISTERED_RUNNER_KINDS and len(s.runtime_pins)==4"),
            env=host_env, capture_output=True, text=True, timeout=30,
            check=False)
        if host_check.returncode:
            raise InstallError("HOST_PROOF:" + host_check.stderr[-240:])
        guest_check = subprocess.run(("pct", "exec", "110", "--",
            "/usr/bin/env", "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=" + GUEST_ROOT, "/usr/bin/python3", "-B", "-c",
            "import aster_llama_sa3_candidate_j_quality_wrapper as w;"
            "import sa3_evidence_matrix_candidate_j_quality_runtime as q;"
            "import sa3_evidence_matrix_candidate_j_runner as r;"
            "assert len(w.PINS)==4 and callable(q.run_quality) and callable(r.run_case)"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_check.returncode:
            raise InstallError("GUEST_PROOF:" + guest_check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive",
                "host_replaced": len(HOST_REPLACE),
                "host_added": len(HOST_ADD), "guest": guest_value,
                "manifest_pins": 46, "checkpoint": "retained",
                "service_restart": False, "workload_effect": "not-attempted",
                "booking": "absent"}
    except BaseException:
        if guest_started:
            _guest("rollback")
        for name, (new, _) in reversed(tuple(HOST_ADD.items())):
            target = HOST_ROOT / name
            if os.path.lexists(target):
                if digest(regular(target)) != new:
                    raise InstallError("ROLLBACK_UNCERTAIN:" + name)
                target.unlink()
        for name, (_, _, mode) in reversed(tuple(HOST_REPLACE.items())):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), mode)
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
