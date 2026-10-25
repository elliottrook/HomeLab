"""Independent deadline/recovery boundary for the evaluation lease.

The default CLI path is inert.  A future installed watchdog must supply an
effect-authorized recovery adapter explicitly; otherwise it reports disabled
without reading or mutating lease state.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from evaluation_lease import watchdog_decision


def run_once(*, now_epoch: int, heartbeat_epoch: int, heartbeat_timeout: int,
             hard_deadline_epoch: int, restore_deadline_epoch: int,
             owner_present: bool, effect_authorized: bool,
             recovery: Callable[[], object] | None = None) -> dict[str, object]:
    decision = watchdog_decision(
        now_epoch=now_epoch, heartbeat_epoch=heartbeat_epoch,
        heartbeat_timeout=heartbeat_timeout,
        hard_deadline_epoch=hard_deadline_epoch,
        restore_deadline_epoch=restore_deadline_epoch,
        owner_present=owner_present,
    )
    if decision.action == "continue":
        return {"effects": "not-attempted", "decision": decision.reason}
    if not effect_authorized or recovery is None:
        return {"effects": "disabled", "decision": decision.reason}
    try:
        result = recovery()
    except Exception:
        return {"effects": "uncertain", "decision": decision.reason}
    return {"effects": "recovered", "decision": decision.reason, "result": result}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    del args
    print(json.dumps({"effects": "disabled", "state": "source-only"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
