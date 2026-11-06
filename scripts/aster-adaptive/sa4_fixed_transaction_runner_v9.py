"""SA4 v9 runner with fresh v6 state after pre-owner v8 reconciliation."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import sys, time
import sa4_fixed_transaction_runner_v8 as previous

INPUT_DIR=Path("/var/lib/aster/sa4/transaction-input-v6")
EVIDENCE_DIR=Path("/var/lib/aster/sa4/transaction-evidence-v6")
LEDGER_ROOT=Path("/var/lib/aster/sa4/one-use-ledger-v6")
OPERATION_ID="sa4-canary-v2-fifth-operation-v1"
EXPECTED_PREDECESSOR=(Path("/var/lib/aster/sa4/transaction-input-v5"),
 Path("/var/lib/aster/sa4/transaction-evidence-v5"),
 Path("/var/lib/aster/sa4/one-use-ledger-v5"),
 "sa4-canary-v2-fourth-operation-v1")

@contextmanager
def _fresh_paths():
    originals=(previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID)
    if originals != EXPECTED_PREDECESSOR: raise ValueError("SA4 v9 predecessor changed")
    previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID=(INPUT_DIR,EVIDENCE_DIR,LEDGER_ROOT,OPERATION_ID)
    try: yield
    finally: previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID=originals

def execute(now:int):
    if type(now) is not int or now < 1: raise ValueError("SA4 v9 time changed")
    with _fresh_paths(): return previous.execute(now)

def main(arguments):
    if arguments: raise ValueError("SA4 v9 runner accepts no arguments")
    execute(int(time.time())); return 0

if __name__ == "__main__":
    try: raise SystemExit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError) as error:
        print(f"error: {error}",file=sys.stderr); raise SystemExit(1)
