"""Fixed SA4 successor using fresh paths after the retained v4 NO-GO."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
import time

import sa4_distinct_registry_bindings_v1 as bindings
import sa4_fixed_transaction_runner_v3 as previous
import sa4_root_transaction_owner_v5 as root_owner


INPUT_DIR = Path("/var/lib/aster/sa4/transaction-input-v3")
EVIDENCE_DIR = Path("/var/lib/aster/sa4/transaction-evidence-v3")
LEDGER_ROOT = Path("/var/lib/aster/sa4/one-use-ledger-v3")
OPERATION_ID = "sa4-canary-v2-second-operation-v1"
EXPECTED_PREDECESSOR = (
    Path("/var/lib/aster/sa4/transaction-input-v2"),
    Path("/var/lib/aster/sa4/transaction-evidence-v2"),
    Path("/var/lib/aster/sa4/one-use-ledger-v2"),
    "sa4-canary-v2-first-operation-v1",
)


@contextmanager
def _fresh_paths():
    originals = (previous.INPUT_DIR, previous.EVIDENCE_DIR,
                 previous.LEDGER_ROOT, previous.OPERATION_ID)
    if originals != EXPECTED_PREDECESSOR:
        raise ValueError("SA4 v6 predecessor paths changed")
    previous.INPUT_DIR = INPUT_DIR
    previous.EVIDENCE_DIR = EVIDENCE_DIR
    previous.LEDGER_ROOT = LEDGER_ROOT
    previous.OPERATION_ID = OPERATION_ID
    try:
        yield
    finally:
        (previous.INPUT_DIR, previous.EVIDENCE_DIR,
         previous.LEDGER_ROOT, previous.OPERATION_ID) = originals


def execute(now_epoch: int) -> dict[str, object]:
    if type(now_epoch) is not int or now_epoch < 1:
        raise ValueError("SA4 v6 runner time changed")
    original_owner = previous.root_owner
    if original_owner.__name__ != "sa4_root_transaction_owner_v3":
        raise ValueError("SA4 v6 runner predecessor owner changed")
    if root_owner.BOUND_TARGET_ID != bindings.TARGET_ID:
        raise ValueError("SA4 v6 runner target interface changed")
    with _fresh_paths():
        plan_raw = previous._read("plan")
        with bindings.accepted_registry(plan_raw):
            previous.root_owner = root_owner
            try:
                return previous.execute(now_epoch)
            finally:
                previous.root_owner = original_owner


def main(arguments: list[str]) -> int:
    if arguments:
        raise ValueError("SA4 v6 runner accepts no arguments")
    execute(int(time.time()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
