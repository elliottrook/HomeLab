"""Correct nested canonical JSON decoding for the exact v9 reconciler."""
from __future__ import annotations
from contextlib import contextmanager
import os, sys, time
import sa4_registration_mismatch_reconciler_v1 as previous
import sa4_single_file_repair_contract_v1 as contract

def _json(raw: bytes) -> dict[str, object]:
    value=contract.decode_unique_json(raw)
    if not isinstance(value,dict) or raw!=contract.canonical(value):
        raise ValueError("SA4 registration reconciliation JSON noncanonical")
    return value
@contextmanager
def _binding():
    original=previous._json
    if original.__module__!=previous.__name__: raise ValueError("SA4 reconciler predecessor changed")
    previous._json=_json
    try: yield
    finally: previous._json=original
def reconcile(observed_epoch:int):
    with _binding(): return previous.reconcile(observed_epoch)
def main(args):
    if args: raise ValueError("SA4 registration reconciler v2 accepts no arguments")
    os.write(1,reconcile(int(time.time()))); return 0
if __name__=="__main__":
    try: raise SystemExit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError) as e: print(f"error: {e}",file=sys.stderr); raise SystemExit(1)
