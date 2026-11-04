"""Reversibly install candidate-g response normalization inactive."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import subprocess

from sa3_evidence_envelope_inactive_install import (
    GUEST_ROOT, HOST_ROOT, InstallError, atomic, digest, regular, source,
)
from sa3_candidate_g_diagnostic_inactive_install import _quiet


CHECKPOINT = Path(
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-g-response-normalization-r1-20261104")
GUEST_CHECKPOINT = str(CHECKPOINT)
HOST_FILES = {
    "lab_hours_workloads.py": (
        "3bcfefd8942bbc8f31db70bce51a04ff17ce2f13adb352d816ae6cdd7237be73",
        "49fc9ebfb703437e4735093e5f0ed08a1d29ea2fa966b1cf0294b88c9d88a174", 0o644),
    "lab_hours_release_manifest.json": (
        "7bbfd20888675768d544420e2d0a4f06e5c291f5c243c2e5dec3b2aa5d5596f0",
        "8717c42c8bb24f33ee24cf176b11457766b88e5a90723142bad28842978d55a2", 0o644),
}
GUEST_FILES = {
    "sa3_evidence_envelope_runner_v1.py": (
        "22828169293ab013076d42928f38159ac356f3ef8c584419ea4ddff2b43de45b",
        "372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352"),
    "aster_llama_sa3_evidence_envelope_wrapper.py": (
        "626f235bbbecfe74a8f19be547c399881d38568008145a9be75875378fef0abe",
        "1c0240fe7ad1c8f11b22410ecb8938edc6a056007f7f1e578ce0c484ec3c9697"),
}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1]; v=json.loads(sys.stdin.read()); root=Path(v["root"]); cp=Path(v["checkpoint"])
def regular(p,mode):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes()
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".response-normalization")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS:"+p.name)
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data); os.fchmod(fd,mode); os.fchown(fd,0,0); os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,p)
pins=v["pins"]
if op=="preflight":
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 for n,p in pins.items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=p["old"]: raise SystemExit("BASELINE_DRIFT:"+n)
 cp.mkdir(parents=True,mode=0o700); os.chmod(cp,0o700); os.chown(cp,0,0)
 for n,p in pins.items(): atomic(cp/n,regular(root/n,0o644),0o600)
 print("{}")
elif op=="install":
 n=v["name"]; p=pins[n]; data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=p["new"]: raise SystemExit("SOURCE_HASH:"+n)
 if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=p["old"]: raise SystemExit("BASELINE_DRIFT:"+n)
 atomic(root/n,data,0o644); print("{}")
elif op=="verify":
 for n,p in pins.items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=p["new"]: raise SystemExit("POSTCHECK:"+n)
 print(json.dumps({"files":len(pins),"state":"valid"},sort_keys=True))
elif op=="rollback":
 for n,p in pins.items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=p["new"]: raise SystemExit("ROLLBACK_UNCERTAIN:"+n)
  old=regular(cp/n,0o600)
  if hashlib.sha256(old).hexdigest()!=p["old"]: raise SystemExit("CHECKPOINT_DRIFT:"+n)
  atomic(root/n,old,0o644)
 print("{}")
'''


def _guest(op: str, *, name: str | None = None,
           data: bytes | None = None) -> str:
    pins = {item: {"old": old, "new": new}
            for item, (old, new) in GUEST_FILES.items()}
    value = {"root": GUEST_ROOT, "checkpoint": GUEST_CHECKPOINT,
             "pins": pins}
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
    _quiet()
    host_data = {}
    for name, (old, new, mode) in HOST_FILES.items():
        current = regular(HOST_ROOT / name, mode)
        if digest(current) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        host_data[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_paths = {
        "sa3_evidence_envelope_runner_v1.py":
            "services/aster-agent/evals/sa3_evidence_envelope_runner_v1.py",
        "aster_llama_sa3_evidence_envelope_wrapper.py":
            "scripts/local-ai/aster_llama_sa3_evidence_envelope_wrapper.py",
    }
    guest_data = {name: source(stage, guest_paths[name], new)
                  for name, (_, new) in GUEST_FILES.items()}
    CHECKPOINT.mkdir(parents=True, mode=0o700); os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, mode) in HOST_FILES.items():
        data = regular(HOST_ROOT / name, mode)
        atomic(CHECKPOINT / name, data, 0o600)
        if digest(data) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    _guest("preflight")
    guest_started = False
    try:
        for name, (_, _, mode) in HOST_FILES.items():
            atomic(HOST_ROOT / name, host_data[name], mode)
        guest_started = True
        for name, (_, new) in GUEST_FILES.items():
            _guest("install", name=name, data=guest_data[name])
        guest_value = json.loads(_guest("verify"))
        for name, (_, new, mode) in HOST_FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != new:
                raise InstallError("POSTCHECK:" + name)
        host_env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                    "PYTHONPATH": str(HOST_ROOT)}
        host_check = subprocess.run(("/usr/bin/python3", "-B", "-c",
            "import lab_hours_reserved_runner as r,lab_hours_workloads as w; "
            "assert len(r.load_manifest())==34; "
            "assert dict(w.workload('sa3-evidence-envelope-quality-v1').runtime_pins)"
            "['sa3_evidence_envelope_runner_v1.py']=='372c19ef3c2f5e8f0965167011c4bba47d9326e5f5ffe7d0b77d9ac5898fc352'"),
            env=host_env, capture_output=True, text=True, timeout=30, check=False)
        if host_check.returncode:
            raise InstallError("HOST_PROOF:" + host_check.stderr[-240:])
        guest_check = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import sa3_evidence_envelope_runner_v1 as r; "
            "v={'choices':[{'message':{'role':'assistant','content':'{\\\"diagnosis\\\":\\\"d\\\",\\\"verification\\\":\\\"v\\\"}'},'finish_reason':'stop','index':0,'logprobs':None,'stop_reason':None}], 'id':'x','object':'chat.completion','created':1,'model':'m','system_fingerprint':'x','usage':{},'timings':{}}; "
            "d,f=r._parse_response(v); assert f=='stop' and set(d)=={'diagnosis','verification'}"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_check.returncode:
            raise InstallError("GUEST_NORMALIZATION_PROOF:" + guest_check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive", "host_files": 2,
                "guest": guest_value, "manifest_pins": 34,
                "checkpoint": "retained", "service_restart": False,
                "workload_effect": "not-attempted"}
    except BaseException:
        if guest_started:
            _guest("rollback")
        for name, (_, _, mode) in reversed(tuple(HOST_FILES.items())):
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), mode)
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
