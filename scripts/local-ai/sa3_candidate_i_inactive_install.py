"""Reversibly install candidate-i inactive without creating a booking."""
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
    "/var/lib/local-ai-lab/checkpoints/sa3-candidate-i-inactive-r1-20261104")
GUEST_CHECKPOINT = str(CHECKPOINT)
UNIT_PREFIX = "aster-lab-hours-booking-sa3-evidence-envelope-candidate-i-quality-v1"
HOST_REPLACE = {
    "lab_hours_workloads.py": (
        "49fc9ebfb703437e4735093e5f0ed08a1d29ea2fa966b1cf0294b88c9d88a174",
        "829024378e11ec98ff67dc42d1554588f68b4e95f8115532081e29663e87ab70", 0o644),
    "lab_hours_reserved_runner.py": (
        "63c7a116f326161dfb550cb3bfdaf268cbab29820e7b9f0105e810c595a75aba",
        "eab869dae32340d302c25c6346843b94c6d79a539eccf975cfe9d7c69ca47960", 0o755),
    "full_inference_lab_runtime.py": (
        "b4fc31b0eaeab14b0beb81b47103f2d03a62cf9e6bf3bbccdfc4560a0f444da9",
        "6c7767e5a22829d3369b5c385495aea7d2879986c9adb5e698aef29d3df198ad", 0o755),
    "lab_hours_release_manifest.json": (
        "8717c42c8bb24f33ee24cf176b11457766b88e5a90723142bad28842978d55a2",
        "c2812b754c2d5c87156898548d63a407f5afcca7ac7d4000ece645b14a922a5e", 0o644),
}
HOST_ADD = {
    "sa3_candidate_i_evidence_envelope_transaction.py":
        ("c1d40abe685860ba6202ea5b18425a1ba8fbcc5e5aa7e820ae555ec08c922131", 0o644),
    "sa3_candidate_i_evidence_envelope_listener_adapter.py":
        ("e16a251225ca0cc757c74cd3b38641700aeabf9f32391836309ebfe42fd0a8c6", 0o644),
}
GUEST_EXISTING = {
    "sa3_deterministic_evidence_envelope_v1.py":
        "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
}
GUEST_ADD = {
    "sa3-evidence-envelope-candidate-i-quality-v1.json":
        "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0",
    "sa3_deterministic_evidence_envelope_v2.py":
        "4ca154c6ea0b0738adc3c9e21544ac0a6d3c05473852f88f97b6e5e7e1611943",
    "sa3_evidence_envelope_batch_v2.py":
        "eaeddb10d5a36df5dd3f3646691d19857f094f2872086d7b78056d6ff7c70d4e",
    "sa3_evidence_envelope_runner_v2.py":
        "58b932a65afb6d88d4624d3d74b0d4d021091e0989c74e1ca4cf0afdede9188c",
    "aster_llama_sa3_candidate_i_evidence_envelope_wrapper.py":
        "a3db03b8f98f144a34aa15aa173d16275673cb17dd18fc0ce581c685e1b29a74",
}
GUEST_SOURCE_PATHS = {
    "aster_llama_sa3_candidate_i_evidence_envelope_wrapper.py":
        "scripts/local-ai/aster_llama_sa3_candidate_i_evidence_envelope_wrapper.py",
    **{name: "services/aster-agent/evals/" + name
       for name in GUEST_ADD
       if name != "aster_llama_sa3_candidate_i_evidence_envelope_wrapper.py"},
}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1]; v=json.loads(sys.stdin.read()); root=Path(v["root"]); cp=Path(v["checkpoint"])
def regular(p,mode):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes()
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".candidate-i")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS:"+p.name)
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data); os.fchmod(fd,mode); os.fchown(fd,0,0); os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,p)
if op=="preflight":
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 for n,h in v["existing"].items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=h: raise SystemExit("BASELINE_DRIFT:"+n)
 for n in v["add"]:
  if os.path.lexists(root/n): raise SystemExit("TARGET_PRESENT:"+n)
 cp.mkdir(parents=True,mode=0o700); os.chmod(cp,0o700); os.chown(cp,0,0)
 atomic(cp/"guest-manifest.json",(json.dumps({"absent":sorted(v["add"]),"existing":v["existing"]},sort_keys=True)+"\n").encode(),0o600)
 print("{}")
elif op=="install":
 n=v["name"]; data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=v["add"][n]: raise SystemExit("SOURCE_HASH:"+n)
 if os.path.lexists(root/n): raise SystemExit("TARGET_PRESENT:"+n)
 atomic(root/n,data,0o644); print("{}")
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

    CHECKPOINT.mkdir(parents=True, mode=0o700); os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, mode) in HOST_REPLACE.items():
        data = regular(HOST_ROOT / name, mode)
        atomic(CHECKPOINT / name, data, 0o600)
        if digest(data) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    atomic(CHECKPOINT / "host-manifest.json",
           (json.dumps({"absent": sorted(HOST_ADD),
                        "replaced": sorted(HOST_REPLACE)}, sort_keys=True) + "\n").encode(),
           0o600)
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
            "import sa3_candidate_i_evidence_envelope_transaction;"
            "import sa3_candidate_i_evidence_envelope_listener_adapter;"
            "assert len(r.load_manifest())==36;"
            "s=w.workload('sa3-evidence-envelope-candidate-i-quality-v1');"
            "assert s.runner_kind in r.REGISTERED_RUNNER_KINDS and len(s.runtime_pins)==5"),
            env=host_env, capture_output=True, text=True, timeout=30, check=False)
        if host_check.returncode:
            raise InstallError("HOST_PROOF:" + host_check.stderr[-240:])
        guest_check = subprocess.run(("pct", "exec", "110", "--", "/usr/bin/env",
            "PYTHONDONTWRITEBYTECODE=1", "PYTHONPATH=" + GUEST_ROOT,
            "/usr/bin/python3", "-B", "-c",
            "import aster_llama_sa3_candidate_i_evidence_envelope_wrapper as w;"
            "import sa3_evidence_envelope_batch_v2 as b;"
            "import sa3_evidence_envelope_runner_v2 as r;"
            "v={'choices':[{'message':{'role':'assistant','content':'{\"diagnosis\":\"bounded\"}'},'finish_reason':'stop','index':0,'logprobs':None,'stop_reason':None}], 'id':'x','object':'chat.completion','created':1,'model':'m','system_fingerprint':'x','usage':{},'timings':{}};"
            "d,f=r._parse_response(v);assert f=='stop' and set(d)=={'diagnosis'};"
            "assert len(w.PINS)==5 and b.PACKET_SHA256==w.PINS['sa3-evidence-envelope-candidate-i-quality-v1.json']"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_check.returncode:
            raise InstallError("GUEST_PROOF:" + guest_check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive",
                "host_replaced": len(HOST_REPLACE), "host_added": len(HOST_ADD),
                "guest": guest_value, "manifest_pins": 36,
                "checkpoint": "retained", "service_restart": False,
                "workload_effect": "not-attempted", "booking": "absent"}
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
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--apply", action="store_true"); args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"},
                         sort_keys=True)); return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True)); return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True)); return 1


if __name__ == "__main__":
    raise SystemExit(main())
