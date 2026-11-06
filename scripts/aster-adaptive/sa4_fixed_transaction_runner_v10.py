"""SA4 v10 fixes the core runner's omitted registry-v3 alias binding."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import sys,time
import sa4_fixed_transaction_runner_v3 as core
import sa4_fixed_transaction_runner_v9 as previous
import sa4_target_registry_v2 as registry_v2
import sa4_target_registry_v3 as registry_v3
INPUT_DIR=Path("/var/lib/aster/sa4/transaction-input-v7");EVIDENCE_DIR=Path("/var/lib/aster/sa4/transaction-evidence-v7");LEDGER_ROOT=Path("/var/lib/aster/sa4/one-use-ledger-v7");OPERATION_ID="sa4-canary-v2-sixth-operation-v1"
EXPECTED_PREDECESSOR=(Path("/var/lib/aster/sa4/transaction-input-v6"),Path("/var/lib/aster/sa4/transaction-evidence-v6"),Path("/var/lib/aster/sa4/one-use-ledger-v6"),"sa4-canary-v2-fifth-operation-v1")
@contextmanager
def _bindings():
    original=(previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID,core.registry)
    if original[:4]!=EXPECTED_PREDECESSOR or original[4] is not registry_v2: raise ValueError("SA4 v10 predecessor binding changed")
    previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID=INPUT_DIR,EVIDENCE_DIR,LEDGER_ROOT,OPERATION_ID;core.registry=registry_v3
    try: yield
    finally: previous.INPUT_DIR,previous.EVIDENCE_DIR,previous.LEDGER_ROOT,previous.OPERATION_ID,core.registry=original
def execute(now):
    if type(now)is not int or now<1: raise ValueError("SA4 v10 time changed")
    with _bindings(): return previous.execute(now)
def main(args):
    if args: raise ValueError("SA4 v10 runner accepts no arguments")
    execute(int(time.time())); return 0
if __name__=="__main__":
    try: raise SystemExit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError) as e: print(f"error: {e}",file=sys.stderr); raise SystemExit(1)
