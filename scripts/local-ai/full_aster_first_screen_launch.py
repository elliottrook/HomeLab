"""One-shot launcher for the approved full-Aster first-screen transaction."""
from __future__ import annotations

import argparse
from datetime import datetime, time as wall_time
import json
import os
from pathlib import Path
import secrets
import subprocess
import time
from zoneinfo import ZoneInfo

from full_aster_first_screen_guardian import ARMED, FULL_DRAIN_STATE, STATE


ROOT = "/usr/local/libexec/local-ai-lease/full-inference-pilot"
ZONE = ZoneInfo("America/Vancouver")
RUN_DATE = "2026-10-27"
EARLIEST = wall_time(3, 10)
LATEST = wall_time(3, 30)
PROTECTED = wall_time(4, 15)
EFFECT_SECONDS = 30 * 60
RECOVERY_SECONDS = 15 * 60


def window_deadlines(started: int) -> tuple[int, int]:
    """Bind relative guardian deadlines to the approved Vancouver window."""
    if type(started) is not int or started <= 0:
        raise ValueError("first-screen start time is invalid")
    local = datetime.fromtimestamp(started, ZONE)
    if local.strftime("%Y-%m-%d") != RUN_DATE or not EARLIEST <= local.time() <= LATEST:
        raise ValueError("first-screen start is outside the approved window")
    protected = int(datetime.combine(local.date(), PROTECTED, tzinfo=ZONE).timestamp())
    rescue_at = started + EFFECT_SECONDS
    hard_deadline = min(started + EFFECT_SECONDS + RECOVERY_SECONDS, protected)
    if hard_deadline - rescue_at < RECOVERY_SECONDS:
        raise ValueError("first-screen recovery reserve is unavailable")
    return rescue_at, hard_deadline


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
    try: rescue_at, hard_deadline = window_deadlines(started)
    except ValueError as error: raise SystemExit(str(error)) from error
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
