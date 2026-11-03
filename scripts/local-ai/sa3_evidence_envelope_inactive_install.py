"""Install the fixed candidate-g registration and dormant LXC110 runtime."""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess


HOST_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
GUEST_ROOT = "/usr/local/libexec/local-ai-lease/full-inference-pilot"
CHECKPOINT = Path("/var/lib/local-ai-lab/checkpoints/sa3-evidence-envelope-inactive-v1")
GUEST_CHECKPOINT = "/var/lib/local-ai-lab/checkpoints/sa3-evidence-envelope-inactive-v1"
GUEST_ID = "110"
UNIT_PREFIX = "aster-lab-hours-booking-sa3-evidence-envelope-quality-v1"

HOST_FILES = {
    "lab_hours_workloads.py": (
        "94d70bbd5c1b791b70c76f6c78a9ce55d81922958520c9f1f68de4ee4013bedf",
        "3bcfefd8942bbc8f31db70bce51a04ff17ce2f13adb352d816ae6cdd7237be73", 0o644),
    "lab_hours_inactive_target.py": (
        "fd467544649cc877ca06f831d8f84aaca495416c19072256bd228fc11601ae33",
        "a99c1f8669836513a8dcc51d9a80182be4ad08b6db3be1c09b48ea727a831e47", 0o644),
    "lab_hours_release_manifest.json": (
        "d853b0f05382d1cebfd6c6d9a1d30068e3d6295a918f62ac41bea6ff1e2a0951",
        "36e2024248e1c64a9c3448db6b12efff3fcc1228dd867aba3ebf8248b9d0d84d", 0o644),
}

GUEST_FILES = {
    "sa3-evidence-envelope-quality-v1.json":
        "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
    "sa3_deterministic_evidence_envelope_v1.py":
        "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
    "sa3_evidence_envelope_batch_v1.py":
        "78abc29951fe80a469c49ee44af6a9380f032648ad757f3182c11bd0f0464500",
    "sa3_evidence_envelope_quality_freeze_v1.py":
        "95cf006fc7e3b2aeb3acf0e926336e65e3c3a8b5e5f8cb5cc083e4e5ab7b3483",
    "sa3_evidence_envelope_runner_v1.py":
        "22828169293ab013076d42928f38159ac356f3ef8c584419ea4ddff2b43de45b",
}

REMOTE = r'''import base64,hashlib,json,os,stat,sys
from pathlib import Path
op=sys.argv[1]; v=json.loads(sys.stdin.read()); root=Path(v["root"])
def regular(p):
 s=p.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=0 or s.st_nlink!=1: raise SystemExit("CUSTODY:"+p.name)
 return p.read_bytes(),s
def atomic(p,data,mode):
 t=p.parent/("."+p.name+".candidate-g")
 if os.path.lexists(t): raise SystemExit("TEMP_EXISTS:"+p.name)
 fd=os.open(t,os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW,0o600)
 try: os.write(fd,data); os.fchmod(fd,mode); os.fchown(fd,0,0); os.fsync(fd)
 finally: os.close(fd)
 os.replace(t,p)
if op=="preflight":
 for n in v["pins"]:
  if os.path.lexists(root/n): raise SystemExit("TARGET_PRESENT:"+n)
 cp=Path(v["checkpoint"])
 if os.path.lexists(cp): raise SystemExit("CHECKPOINT_EXISTS")
 cp.mkdir(parents=True,mode=0o700); os.chmod(cp,0o700); os.chown(cp,0,0)
 atomic(cp/"manifest.json",(json.dumps({"absent":sorted(v["pins"])},sort_keys=True)+"\n").encode(),0o600)
 print("{}")
elif op=="install":
 p=root/v["name"]; data=base64.b64decode(v["data"])
 if hashlib.sha256(data).hexdigest()!=v["sha256"]: raise SystemExit("SOURCE_HASH:"+v["name"])
 if os.path.lexists(p): raise SystemExit("TARGET_PRESENT:"+v["name"])
 atomic(p,data,0o644); print("{}")
elif op=="verify":
 for n,h in v["pins"].items():
  data,s=regular(root/n)
  if stat.S_IMODE(s.st_mode)!=0o644 or hashlib.sha256(data).hexdigest()!=h: raise SystemExit("VERIFY:"+n)
 print(json.dumps({"files":len(v["pins"]),"state":"valid"},sort_keys=True))
elif op=="rollback":
 for n,h in v["pins"].items():
  p=root/n
  if os.path.lexists(p):
   data,s=regular(p)
   if hashlib.sha256(data).hexdigest()!=h: raise SystemExit("ROLLBACK_UNCERTAIN:"+n)
   p.unlink()
 print("{}")
'''


class InstallError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, mode: int | None = None) -> bytes:
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1
            or (mode is not None and stat.S_IMODE(info.st_mode) != mode)):
        raise InstallError("CUSTODY:" + path.name)
    return path.read_bytes()


def atomic(path: Path, data: bytes, mode: int) -> None:
    temporary = path.parent / ("." + path.name + ".candidate-g")
    if os.path.lexists(temporary):
        raise InstallError("TEMP_EXISTS:" + path.name)
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data)
        os.fchmod(descriptor, mode)
        os.fchown(descriptor, 0, 0)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def guest(op: str, value: dict[str, object]) -> str:
    result = subprocess.run(("pct", "exec", GUEST_ID, "--", "/usr/bin/python3", "-B", "-c", REMOTE, op),
                            input=json.dumps(value), text=True, capture_output=True,
                            timeout=30, check=False)
    if result.returncode:
        raise InstallError("GUEST_" + op.upper() + ":" + (result.stderr or result.stdout).strip()[-240:])
    return result.stdout.strip()


def source(stage: Path, relative: str, expected: str) -> bytes:
    path = stage / relative
    if not path.is_file() or path.is_symlink():
        raise InstallError("SOURCE_MISSING:" + relative)
    data = path.read_bytes()
    if digest(data) != expected:
        raise InstallError("SOURCE_HASH:" + relative)
    return data


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
        current = regular(HOST_ROOT / name, mode)
        if digest(current) != old:
            raise InstallError("BASELINE_DRIFT:" + name)
        host_data[name] = source(stage, "scripts/local-ai/" + name, new)
    guest_data = {
        name: source(stage, "services/aster-agent/evals/" + name, expected)
        for name, expected in GUEST_FILES.items()
    }
    CHECKPOINT.mkdir(parents=True, mode=0o700)
    os.chmod(CHECKPOINT, 0o700)
    for name, (old, _, _) in HOST_FILES.items():
        data = regular(HOST_ROOT / name)
        target = CHECKPOINT / name
        atomic(target, data, 0o600)
        if digest(data) != old:
            raise InstallError("CHECKPOINT_DRIFT:" + name)
    guest("preflight", {"root": GUEST_ROOT, "checkpoint": GUEST_CHECKPOINT,
                         "pins": GUEST_FILES})
    installed_guest = False
    try:
        for name, (_, _, mode) in HOST_FILES.items():
            atomic(HOST_ROOT / name, host_data[name], mode)
        installed_guest = True
        for name, expected in GUEST_FILES.items():
            guest("install", {"root": GUEST_ROOT, "name": name, "sha256": expected,
                              "data": base64.b64encode(guest_data[name]).decode()})
        output = guest("verify", {"root": GUEST_ROOT, "pins": GUEST_FILES})
        for name, (_, new, mode) in HOST_FILES.items():
            if digest(regular(HOST_ROOT / name, mode)) != new:
                raise InstallError("POSTCHECK:" + name)
        env = os.environ.copy()
        env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(HOST_ROOT))
        check = subprocess.run(("/usr/bin/python3", "-B", str(HOST_ROOT / "lab_hours_inactive_target.py"),
                                "--workload", "sa3-evidence-envelope-quality-v1"),
                               env=env, capture_output=True, text=True, timeout=30, check=False)
        if check.returncode:
            raise InstallError("VALIDATOR:" + (check.stderr or check.stdout).strip()[-240:])
        return {"state": "installed-inactive", "registration": "sa3-evidence-envelope-quality-v1",
                "guest": json.loads(output), "effects": "not-attempted", "checkpoint": "retained"}
    except BaseException:
        if installed_guest:
            guest("rollback", {"root": GUEST_ROOT, "pins": GUEST_FILES})
        for name, (_, _, mode) in HOST_FILES.items():
            atomic(HOST_ROOT / name, regular(CHECKPOINT / name, 0o600), mode)
        raise


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if not args.apply:
        print(json.dumps({"state": "source-only", "reason": "--apply required"}, sort_keys=True))
        return 2
    try:
        print(json.dumps(install(args.stage), sort_keys=True))
        return 0
    except (InstallError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
