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
import subprocess
from datetime import datetime, timezone
from pathlib import Path


LINE = re.compile(r"^([🟢🟡🔴])\s+(.+)$")
STATUS = {"🟢": "pass", "🟡": "warn", "🔴": "fail"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Aster's sanitized Doctor summary")
    parser.add_argument("--output", type=Path, required=True, help="root-owned destination JSON file")
    parser.add_argument("--doctor", type=Path, default=Path(__file__).with_name("doctor.sh"))
    args = parser.parse_args()

    completed = subprocess.run([str(args.doctor)], text=True, capture_output=True, check=False)
    checks: list[dict[str, str]] = []
    for line in (completed.stdout + "\n" + completed.stderr).splitlines():
        match = LINE.match(line)
        if match:
            checks.append({"name": "HomeLab Doctor", "status": STATUS[match.group(1)], "summary": match.group(2)[:500]})
    overall = "failed" if completed.returncode else ("warning" if any(c["status"] == "warn" for c in checks) else "healthy")
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
    args.output.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
