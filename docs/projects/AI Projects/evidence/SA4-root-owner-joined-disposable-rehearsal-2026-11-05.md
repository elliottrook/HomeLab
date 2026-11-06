# SA4 root-owner joined disposable rehearsal — 2026-11-05

## Outcome

The former hand-sequenced full-transaction rehearsal now runs through the
single root transaction owner. Both branches passed on a disposable compiled
target:

- success branch: one checkpoint, one claim, one effect, one independent
  observation and one terminal reconciliation; candidate bytes remained and
  the grant was burned uncertain rather than automatically promoted;
- failed-postcheck branch: one checkpoint, one claim, one effect, one verified
  failed observation, one rollback, one independent rollback observation and
  one terminal reconciliation; original bytes were restored and the grant was
  burned failed.

Both paths used fresh runtime controls at the final pre-effect composition,
zero retries and externally generated observer proofs. The owner itself did not
sign, transport, choose a path or accept an effect outcome.

## Verification

- joined root-owner success and rollback branches: 2/2 pass;
- root-owner phase/uncertainty tests: 3/3 pass;
- complete SA4 suite: 137/137 pass;
- whitespace/error check: pass.

The rehearsal used temporary files and test keys only. No production target,
credential, ledger, service, schedule, booking, model or route was changed.

## Next gate

Prepare the exact inactive upgrade packet for the live-preflight, final
admission, root owner and reconciler source set, with installed-hash
predecessors and complete rollback. Installation remains a separate effect
gate. The first real repair remains an immediate exact approval gate.
