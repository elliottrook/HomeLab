"""Fixed SA4 entry point with the complete v5 owner interface."""
from __future__ import annotations

import sys
import time

import sa4_distinct_registry_bindings_v1 as bindings
import sa4_fixed_transaction_runner_v3 as previous
import sa4_root_transaction_owner_v5 as root_owner


def execute(now_epoch: int) -> dict[str, object]:
    if type(now_epoch) is not int or now_epoch < 1:
        raise ValueError("SA4 v5 runner time changed")
    plan_raw = previous._read("plan")
    original_owner = previous.root_owner
    if original_owner.__name__ != "sa4_root_transaction_owner_v3":
        raise ValueError("SA4 v5 runner predecessor owner changed")
    if root_owner.BOUND_TARGET_ID != bindings.TARGET_ID:
        raise ValueError("SA4 v5 runner target interface changed")
    with bindings.accepted_registry(plan_raw):
        previous.root_owner = root_owner
        try:
            return previous.execute(now_epoch)
        finally:
            previous.root_owner = original_owner


def main(arguments: list[str]) -> int:
    if arguments:
        raise ValueError("SA4 v5 runner accepts no arguments")
    execute(int(time.time()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
