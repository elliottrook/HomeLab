"""No-effect validation for a registered Lab Hours workload installation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from lab_hours_workloads import validate_inactive_target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pilot-root", type=Path, required=True)
    parser.add_argument("--unit-root", type=Path, default=Path("/etc/systemd/system"))
    args = parser.parse_args(argv)
    try:
        print(json.dumps(validate_inactive_target(args.pilot_root, unit_root=args.unit_root),
                         sort_keys=True))
    except (OSError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
