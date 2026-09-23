#!/usr/bin/env python3
"""Create the bounded health summary that Aster may read.

The report intentionally contains only Doctor's pass/warn/fail lines and its
aggregate outcome.  It never publishes raw command output, environment values,
credentials, or a way for Aster to execute Doctor itself.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LINE = re.compile(r"^([🟢🟡🔴])\s+(.+)$")
STATUS = {"🟢": "pass", "🟡": "warn", "🔴": "fail"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Aster's sanitized Doctor summary")
    parser.add_argument("--output", type=Path, required=True, help="root-owned destination JSON file")
    parser.add_argument("--doctor", type=Path, default=Path(__file__).with_name("doctor.sh"))
    parser.add_argument("--input", type=Path, help="Reuse a captured Doctor output file instead of running Doctor")
    parser.add_argument("--exit-code", type=int, default=0, help="Exit code of the captured Doctor run")
    parser.add_argument("--publish", action="store_true", help="Publish to the existing Aster health path via Proxmox")
    args = parser.parse_args()

    if args.input:
        completed = subprocess.CompletedProcess([], args.exit_code, args.input.read_text(), "")
    else:
        try:
            completed = subprocess.run([str(args.doctor)], text=True, capture_output=True, check=False, timeout=900)
        except subprocess.TimeoutExpired:
            completed = subprocess.CompletedProcess([], 1, "🔴 Doctor timed out; health collection is incomplete.", "")
    checks: list[dict[str, str]] = []
    for line in (completed.stdout + "\n" + completed.stderr).splitlines():
        match = LINE.match(line)
        if match:
            checks.append({"name": "HomeLab Doctor", "status": STATUS[match.group(1)], "summary": match.group(2)[:500]})
    if not checks:
        checks.append({"name": "HomeLab Doctor", "status": "fail", "summary": "Doctor produced no recognizable checks; health collection is incomplete."})
    overall = "failed" if completed.returncode or any(c["status"] == "fail" for c in checks) else ("warning" if any(c["status"] == "warn" for c in checks) else "healthy")
    # Preserve actionable states if Doctor grows beyond the report-size cap.
    selected_checks = [check for check in checks if check["status"] != "pass"]
    selected_checks.extend(check for check in checks if check["status"] == "pass")
    if completed.returncode and not selected_checks:
        selected_checks.append({"name": "HomeLab Doctor", "status": "fail", "summary": "Doctor exited unsuccessfully; use the operator report for details."})
    report = {
        "schema": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": overall,
        "checks": selected_checks[:32],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n"
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(args.output)
    if args.publish:
        # Fixed destination and commands; the JSON goes over stdin, never shell interpolation.
        writer = """import grp,json,os,pathlib,sys
value=json.load(sys.stdin)
assert value['schema']==1 and value['status'] in ('healthy','warning','failed')
assert isinstance(value['checks'],list) and len(value['checks'])<=32
root=pathlib.Path('/var/lib/aster/health'); root.mkdir(exist_ok=True)
target=root/'latest.json'; temp=root/'latest.json.new'
with temp.open('w') as stream: json.dump(value,stream,separators=(',',':'))
os.chmod(temp,0o640); os.chown(temp,0,grp.getgrnam('aster').gr_gid)
os.replace(temp,target)
"""
        remote = "pct exec 104 -- python3 -c " + shlex.quote(writer)
        subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                        "root@192.168.50.10", remote], input=payload, text=True, check=True, timeout=30)
    return 0 if args.input else completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
