"""One-shot launcher for the approved full-Aster first-screen transaction."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import time

from full_aster_first_screen_guardian import ARMED, FULL_DRAIN_STATE, STATE


ROOT = "/usr/local/libexec/local-ai-lease/full-inference-pilot"


def guardian_command(token: str, owner_unit: str, rescue_at: int, hard_deadline: int):
    return ("systemd-run", "--quiet", "--collect",
        f"--unit=aster-full-screen-guardian-{token}.service",
        "--property=User=root", "--property=Restart=no",
        "/usr/bin/python3", "-B", f"{ROOT}/full_aster_first_screen_guardian.py",
        "--owner-unit", owner_unit, "--rescue-at", str(rescue_at),
        "--hard-deadline", str(hard_deadline), "--effect-authorized")


def owner_command(owner_id: str, owner_unit: str):
    return ("systemd-run", "--quiet", "--collect", "--wait", "--pipe", "--scope",
        f"--unit={owner_unit}", "/usr/bin/python3", "-B",
        f"{ROOT}/full_aster_first_screen_controller.py", "--owner-id", owner_id,
        "--owner-unit", owner_unit, "--effect-authorized")


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-authorized", action="store_true")
    args=parser.parse_args(argv)
    if not args.effect_authorized:
        print(json.dumps({"state":"disabled","effects":"not-attempted"},sort_keys=True)); return 0
    if os.geteuid()!=0 or any(os.path.lexists(path) for path in (ARMED,STATE,FULL_DRAIN_STATE)):
        raise SystemExit("first-screen launcher prestate is not clear")
    token=secrets.token_hex(8); owner_id=f"aster-full-screen-owner-{token}"
    owner_unit=owner_id+".scope"; started=int(time.time())
    rescue_at=started+30*60; hard_deadline=started+45*60
    guardian=subprocess.run(guardian_command(token,owner_unit,rescue_at,hard_deadline),
        capture_output=True,text=True,timeout=30,check=False)
    if guardian.returncode!=0 or guardian.stderr: raise SystemExit("guardian unit did not start")
    deadline=time.monotonic()+20
    while not ARMED.exists():
        if time.monotonic()>=deadline: raise SystemExit("guardian did not publish armed state")
        time.sleep(.2)
    owner=subprocess.run(owner_command(owner_id,owner_unit),capture_output=True,text=True,
                         timeout=90*60,check=False)
    if owner.returncode!=0 or owner.stderr:
        print(json.dumps({"state":"failed","owner_unit":owner_unit},sort_keys=True)); return 1
    print(owner.stdout.strip()); return 0


if __name__=="__main__": raise SystemExit(main())
