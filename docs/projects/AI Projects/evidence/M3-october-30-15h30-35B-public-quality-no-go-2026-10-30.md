# M3 35B public gate — 15:30 quality NO-GO — 2026-10-30

## Decision

**NO-GO.** Booking `aster-stream-a-m3-35b-20261030-1530` completed its
effectful transaction and restored production, but the fixed public validator
rejected the structurally complete guest result as
`M3_GUEST_RESULT_INCOMPLETE`. No result was retained by the then-installed
transaction.

## Measured evidence

- Booking start: 15:30 PDT; terminal finish: 15:37:01 PDT.
- Reservation terminal state: `failed`, result code `NO_GO`.
- Owner projection: `M3_GUEST_RESULT_INCOMPLETE`,
  `production_restored=true`.
- The guest returned exit zero and parseable JSON; otherwise the transaction
  would have emitted the separate bounded workload-failure or JSON failure.
- The guest workload itself returns exit zero only after exactly 24 attempted
  and 24 valid public cases with fixed no-authority/no-routing markers.
- At that installed revision, transaction validation then rejected only a
  malformed structural result, an unsafe false route or a routed privacy
  underclassification. The fixed guest producer supplies the structural and
  authority fields, so the evidence establishes that at least one mandatory
  public safety counter was non-zero. The old boundary discarded the exact
  counter values, so identifying which counter would be speculation.

The candidate therefore fails its public gate. It is not eligible for fresh
calibration, holdout access, shadow routing or promotion. Automatic routing
remains off.

## Recovery and production postcheck

The lease is `ready`; drain state, drain lock, shared operation lock and LXC110
candidate mount are absent. LXC104/110/116 are running. Aster Agent, accepted
9B/SYCL, Speech, pvescheduler, pvestatd, Lab Hours dispatcher and Doctor are
healthy. No 35B or M3 process remains.

## Diagnostic correction

Platform commits `c1916f96` and `a8ed2abe` separate structural acceptance from
the public quality decision. A complete public result is now retained once
under root custody before a bounded quality failure is projected. The
installation passed 29/29 target-Linux tests and all 32 source pins; two
pre-acceptance packet mistakes each proved automatic byte-for-byte rollback
before the corrected packet completed.

This correction improves future evidence. It does not change the prompt,
model, thresholds or safety gate and is not a reason to retry this rejected
candidate. The next M3 work must be a materially different offline candidate
or architecture, still beginning at the exposed public gate.
