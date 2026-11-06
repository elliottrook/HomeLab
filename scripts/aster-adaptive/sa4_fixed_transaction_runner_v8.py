"""SA4 successor using a unique plan identity and fresh v5 paths."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys
import time

import sa4_fixed_transaction_runner_v7 as previous


INPUT_DIR = Path("/var/lib/aster/sa4/transaction-input-v5")
EVIDENCE_DIR = Path("/var/lib/aster/sa4/transaction-evidence-v5")
LEDGER_ROOT = Path("/var/lib/aster/sa4/one-use-ledger-v5")
OPERATION_ID = "sa4-canary-v2-fourth-operation-v1"
EXPECTED_PREDECESSOR = (
    Path("/var/lib/aster/sa4/transaction-input-v4"),
    Path("/var/lib/aster/sa4/transaction-evidence-v4"),
    Path("/var/lib/aster/sa4/one-use-ledger-v4"),
    "sa4-canary-v2-third-operation-v1",
)


@contextmanager
def _fresh_paths():
    originals = (previous.INPUT_DIR, previous.EVIDENCE_DIR,
                 previous.LEDGER_ROOT, previous.OPERATION_ID)
    if originals != EXPECTED_PREDECESSOR:
        raise ValueError("SA4 v8 predecessor paths changed")
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
        raise ValueError("SA4 v8 runner time changed")
    with _fresh_paths():
        return previous.execute(now_epoch)


def main(arguments: list[str]) -> int:
    if arguments:
        raise ValueError("SA4 v8 runner accepts no arguments")
    execute(int(time.time()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
