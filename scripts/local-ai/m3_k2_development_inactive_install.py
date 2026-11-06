"""Reversibly install K2 development inactive without a booking."""
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
    "/var/lib/local-ai-lab/checkpoints/m3-k2-development-v1-20261106")
GUEST_CHECKPOINT = str(CHECKPOINT)
UNIT_PREFIX = "aster-lab-hours-booking-m3-k2-shortlist-arbitration-development-v1"
HOST_REPLACE = {
    "lab_hours_workloads.py": (
        "a6a6acb58de8ca8fee2246522aa8e2aa3ebb7d57db2348d694238e4cffbcdfec",
        "ca793b300bd4cb48d5003cbeb3f30a94e981d1c3557472408110e411332167be", 0o755),
    "lab_hours_reserved_runner.py": (
        "4d28ccc44db8a343aa0a1e4baea87d4964bced7db53154f627b5904f7270b11b",
        "9619982232a85c77307f56223b4a5e775882e65dc1886d2aa8a52a23b7eb0849", 0o755),
    "full_inference_lab_runtime.py": (
        "cddae0e3da7ad3c6c6b11b5fb2503f54dec916815e3eb336e13bed74c16b2f61",
        "c52870b880270511495189f4adcb7dd89e34fc199449fe4beb237a754f34be22", 0o755),
    "lab_hours_release_manifest.json": (
        "908b4fe5cd39fca781305913b426e8f6de5991e9246ba4ac16cab15ad9f2f64e",
        "5ecc95ab0a457571f3453feaa0ef2dbece39689c21e4fe30b3031268333840a3", 0o600),
}
HOST_ADD = {
    "m3_k2_development_transaction.py":
        ("67409aa431d2cc6b2ea4dd01d67a0f049b7f2b84e4866f4901285c3739212ec3", 0o644),
    "m3_k2_development_listener_adapter.py":
        ("772415ba38454d3b876f999be404ff6c8aff70cf8e69b3689f5ea45ce4b39fae", 0o644),
    "aster_llama_m3_k2_development_wrapper.py":
        ("12f86fdf694866a08cc0dbd31341d26cb0bec352901bda0241167afe746dd531", 0o644),
}
GUEST_EXISTING = {
    "nlu_deterministic_guard_v1.py": "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135",
    "nlu_local_model_adapter.py": "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0",
    "nlu_threshold_policy.py": "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d",
    "nlu_whole_label_choice_v1.py": "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a",
}
GUEST_ADD = {
    "nlu_k2_consensus_policy_v1.py": "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e",
    "nlu_k2_development_runner_v1.py": "d5c9ef87bd49185466a12e7b53eab741d0f0dc40ce92c2977389dd2b0e5e3785",
    "nlu_k2_development_scorer_v1.py": "c43f3894ba65251b6fadbda1012bd2aead44c3357323b09f491f590ffd6e8558",
    "nlu_k2_shortlist_arbitration_preregistration_v1.py": "f3e633ac81d32bd63fb53e5a51339787cab1e66ee65f56874c012132a32f4f6a",
    "nlu_k2_shortlist_arbitrator_v1.py": "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962",
    "nlu-k2-runtime-manifest-v1.json": "619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88",
    "nlu-k2-development-corpus-v1.json": "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
    "nlu-k2-shortlist-v1.json": "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e",
    "aster_llama_m3_k2_development_wrapper.py": "12f86fdf694866a08cc0dbd31341d26cb0bec352901bda0241167afe746dd531",
}
GUEST_SOURCE_PATHS = {
    "aster_llama_m3_k2_development_wrapper.py":
        "scripts/local-ai/aster_llama_m3_k2_development_wrapper.py",
    "nlu-k2-development-corpus-v1.json": "artifacts/nlu-k2-development-corpus-v1.json",
    "nlu-k2-shortlist-v1.json": "artifacts/nlu-k2-shortlist-v1.json",
    "nlu-k2-runtime-manifest-v1.json":
        "scripts/aster-adaptive/fixtures/nlu-k2-runtime-manifest-v1.json",
    **{name: "scripts/aster-adaptive/" + name for name in GUEST_ADD
       if name not in {"aster_llama_m3_k2_development_wrapper.py",
                       "nlu-k2-development-corpus-v1.json",
                       "nlu-k2-shortlist-v1.json",
                       "nlu-k2-runtime-manifest-v1.json"}},
}
GUEST_MODES = {name: (0o600 if name in {
    "nlu-k2-development-corpus-v1.json", "nlu-k2-shortlist-v1.json"} else 0o644)
    for name in GUEST_ADD}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1];v=json.loads(sys.stdin.read());root=Path(v["root"]);cp=Path(v["checkpoint"])
def regular(p,mode):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1 or stat.S_IMODE(s.st_mode)!=mode: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes()
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".m3-k2")
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
 atomic(root/n,data,v["modes"][n]);print("{}")
elif op=="verify":
 for n,h in v["existing"].items():
  if hashlib.sha256(regular(root/n,0o644)).hexdigest()!=h: raise SystemExit("EXISTING_DRIFT:"+n)
 for n,h in v["add"].items():
  if hashlib.sha256(regular(root/n,v["modes"][n])).hexdigest()!=h: raise SystemExit("POSTCHECK:"+n)
 print(json.dumps({"added":len(v["add"]),"existing":len(v["existing"]),"state":"valid"},sort_keys=True))
elif op=="rollback":
 for n,h in v["add"].items():
  p=root/n
  if os.path.lexists(p):
   if hashlib.sha256(regular(p,v["modes"][n])).hexdigest()!=h: raise SystemExit("ROLLBACK_UNCERTAIN:"+n)
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
             "existing": GUEST_EXISTING, "add": GUEST_ADD,
             "modes": GUEST_MODES}
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
            "import m3_k2_development_transaction;"
            "import m3_k2_development_listener_adapter;"
            "assert len(r.load_manifest())==49;"
            "s=w.workload('m3-k2-shortlist-arbitration-development-v1');"
            "assert s.runner_kind in r.REGISTERED_RUNNER_KINDS and len(s.runtime_pins)==12"),
            env=host_env, capture_output=True, text=True, timeout=30,
            check=False)
        if host_check.returncode:
            raise InstallError("HOST_PROOF:" + host_check.stderr[-240:])
        guest_check = subprocess.run(("pct", "exec", "110", "--",
            "/usr/bin/env", "PYTHONDONTWRITEBYTECODE=1",
            "PYTHONPATH=" + GUEST_ROOT, "/usr/bin/python3", "-B", "-c",
            "import aster_llama_m3_k2_development_wrapper as w;"
            "import nlu_k2_development_runner_v1 as r;"
            "import nlu_k2_development_scorer_v1 as s;"
            "assert len(w.PINS)==12 and callable(r.run_cases) and callable(s.score)"),
            capture_output=True, text=True, timeout=30, check=False)
        if guest_check.returncode:
            raise InstallError("GUEST_PROOF:" + guest_check.stderr[-240:])
        _quiet()
        return {"state": "installed-inactive",
                "host_replaced": len(HOST_REPLACE),
                "host_added": len(HOST_ADD), "guest": guest_value,
                "manifest_pins": 49, "checkpoint": "retained",
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
