"""No-effect validation of the fixed SA3 runtime inside LXC110."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from lab_hours_workloads import workload


GUEST_ID = "110"
GUEST_ROOT = "/usr/local/libexec/local-ai-lease/full-inference-pilot"
UNIT_ROOT = Path("/etc/systemd/system")

GUEST_VALIDATOR = r'''import ast,hashlib,json,os,stat,sys
value=json.loads(sys.stdin.read())
root=value["root"]
pins=value["pins"]
modules={os.path.splitext(n)[0] for n in pins if n.endswith(".py")}
imports=set()
for name,expected in pins.items():
 p=os.path.join(root,name)
 try: s=os.lstat(p)
 except FileNotFoundError: raise SystemExit("TARGET_FILE_MISSING:"+name)
 if (not stat.S_ISREG(s.st_mode) or stat.S_ISLNK(s.st_mode) or s.st_uid != 0
     or s.st_nlink != 1 or hashlib.sha256(open(p,"rb").read()).hexdigest()!=expected):
  raise SystemExit("TARGET_PIN_OR_CUSTODY_MISMATCH:"+name)
 if name.endswith(".py"):
  tree=ast.parse(open(p,encoding="utf-8").read(),filename=p)
  for node in ast.walk(tree):
   if isinstance(node,ast.Import): imports.update(a.name.split(".",1)[0] for a in node.names)
   elif isinstance(node,ast.ImportFrom) and node.level==0 and node.module:
    imports.add(node.module.split(".",1)[0])
missing=sorted(n for n in imports if n in {"sa3_expanded_quality_packet","sa3_expanded_quality_runner","sa3_fair_scorer"} and n not in modules)
if missing: raise SystemExit("UNREGISTERED_LOCAL_DEPENDENCY:"+",".join(missing))
print(json.dumps({"effects":"not-attempted","guest":"110","runtime_files":len(pins),"state":"valid"},sort_keys=True))
'''


def validate_guest_target(*, unit_root: Path = UNIT_ROOT,
                          runner=subprocess.run,
                          workload_id: str = "sa3-expanded-source-quality-v1") -> dict[str, object]:
    spec = workload(workload_id)
    prefix = Path(unit_root) / f"aster-lab-hours-booking-{spec.workload_id}"
    for suffix in (".service", ".timer"):
        if prefix.with_suffix(suffix).exists():
            raise ValueError(f"target unit must remain inactive:{suffix}")
    payload = json.dumps({"root": GUEST_ROOT, "pins": dict(spec.runtime_pins)}, sort_keys=True)
    result = runner(("pct", "exec", GUEST_ID, "--", "/usr/bin/python3", "-B", "-c",
                     GUEST_VALIDATOR), input=payload, capture_output=True, text=True,
                    timeout=30, check=False)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-240:]
        raise ValueError("guest target validation failed:" + detail)
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("guest target validation output invalid") from exc
    expected = {"effects": "not-attempted", "guest": GUEST_ID,
                "runtime_files": len(spec.runtime_pins), "state": "valid"}
    if value != expected:
        raise ValueError("guest target validation result invalid")
    return {"workload_id": spec.workload_id, **value, "target_units": "absent"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", default="sa3-expanded-source-quality-v1",
                        choices=("sa3-expanded-source-quality-v1",
                                 "sa3-evidence-envelope-quality-v1"))
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_guest_target(workload_id=args.workload), sort_keys=True))
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
