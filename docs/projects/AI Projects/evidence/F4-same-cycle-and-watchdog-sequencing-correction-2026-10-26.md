# F4 same-cycle and watchdog sequencing correction — 2026-10-26

## Finding

The October 27 F3 card inherited two mutually incompatible downstream rules:

1. prose deferred F4 to a later backup cycle; but
2. the installed evidence loader and retained-integrity verifier require F2,
   F3 and F4 to bind the same local date and unchanged archive rows.

A successful October 27 F3 receipt would therefore become unusable after
midnight. A second contradiction required the F4 artifact's embedded
`heartbeat_alive` value to be true even though the project tracker arms the
independent evaluation watchdog only at F6, after F4 and F5. The evaluation
adapter cannot create its prepared state and heartbeat until the F4/F5-bound
admission exists, so the old ordering was circular.

## Source correction

Platform commit `970ed2c8` makes the boundaries explicit:

- F4 for Stream A must bind the same local-date F2/F3 archive set after the
  fixed 03:00 pull, using a fresh production observation and separately fixed
  lease identity.
- Generic/full-stop pre-acquire validation remains unchanged and still
  requires a live watchdog.
- Stream A now uses distinctly named `encode_stream_evidence` and
  `decode_stream_evidence` functions. They permit an inactive pre-F6 watchdog
  observation only for the non-effect evidence artifact.
- The effectful controller still calls the original strict validator, and the
  F6 card still requires the independent owner/watchdog before any consumer
  effect.

This is source-only. No installed file, timer, receipt, lease, lock, service or
model changed.

## Verification

The focused F3/F4/F5/evidence-loader/evaluation chain passed 83/83 tests. The
suite proves both sides of the boundary: Stream A evidence can be created
before F6, while the original generic encoder/decoder and effectful controller
continue to reject a missing watchdog.

## Next gate

After a successful October 27 F3 result, produce a reviewed exact-cycle F4/F5
transaction for the same date and obtain separate approval before writing those
artifacts. If F2 or F3 is NO-GO, no F4/F5 transaction may run.
