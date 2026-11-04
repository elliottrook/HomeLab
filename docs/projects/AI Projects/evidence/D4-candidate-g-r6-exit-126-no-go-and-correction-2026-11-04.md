# D4 candidate-g r6 exit-126 NO-GO and correction — 2026-11-04

## Terminal result

Booking `aster-stream-a-sa3-envelope-20261104-1500-r6` is spent and **NO-GO**.
It claimed exactly at 15:00:00 and ended at 15:03:10 after 190 seconds. The
terminal record is `owner-transaction` / `OWNER_TRANSACTION_FAILED_RESTORED`
with `production_restored=true`. No candidate result exists.

The new content-free projection retained:

`candidate-g guest exit-status:126;stdout-bytes:0;stderr-bytes:204`

No raw stderr, prompt, answer, case identity or traceback message was retained.

## Independent restoration

The whole-host lease is ready; Doctor is healthy with zero codes; no drain
state, drain lock, operation lock or port-11436 listener remains. Dispatcher,
Doctor, EPUB scheduler/monitor/worker, `pvescheduler` and `pvestatd` are
healthy. LXC104/110/116 are running; Aster Agent, accepted 9B/SYCL llama and
Speech are active with zero restarts.

## Deterministic cause and source correction

The installed host adapter directly executed the fixed LXC110 Python wrapper.
That wrapper is deliberately root:root mode 0644 with one regular link. Its
shebang does not make a non-executable file directly runnable, so the fixed
`pct exec` command returned status 126 before a listener or model request.

The least-privilege correction keeps the wrapper mode 0644 and inserts only
`/usr/bin/python3 -B` before its exact path. The release manifest is updated to
the new adapter identity. Focused tests pass 9/9, including exact fixed command
shape and 34-pin source identity. A direct target invocation of the installed
0644 wrapper through `/usr/bin/python3 -B ... --help` exits zero without a
listener, model call or state change.

The correction remains source-only until a reversible inactive two-file
installer preserves the exact current adapter/manifest and passes installed
command-shape, lease, lock, Doctor and production proofs. R6 cannot be retried
or sent to blind review.
