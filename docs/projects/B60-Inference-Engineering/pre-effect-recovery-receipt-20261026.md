# Pre-effect recovery and workload binding receipt — 2026-10-26

Nightly trigger 07:33:20 UTC (00:33:20 PDT); measured clock 07:33:30 UTC.
Fetched all known owner refs before admission. Adaptive is now
`99efcf2e119099aa3ed2b9b7537bee4fd553bca7`; platform remains
`6fb0207fec5190e0c34ed3bc72ea38e128f06127`; published B60 and its
protection mirror match `69f302a198615260c40e5228da8a551ec686e25a`.
No fresh complete preflight, lease or workload is admitted by this turn.

## Exact new peer evidence

Under `docs/projects/AI Projects/evidence/` on that Adaptive commit:

| File | SHA-256 |
|---|---|
| `Stream-A-prepare-only-recovery-exercise-pass-2026-10-25.md` | `fc8ee5dedbb6a926f478d9cdfe6b2f18c58c58c3b25c79a2074e3ec05a14a17b` |
| `Stream-A-D4-M3-workload-execution-bindings-2026-10-25.md` | `7fe48d1c28c2ecef1f388a9d18d06dfd1e1c7b2d2748c59fd38904325683558c` |
| `Stream-A-candidate-H-F4-F5-admission-binding-proposal-2026-10-25.md` | `da44f8ebb0d9db31acf41148693744107c869d6eb5fcee788ef4cf7a3bee2453` |

Read the complete three records, current recovery tracker and current delivery
map sections. This supersedes claims that no new recovery implementation or
exercise has occurred. These are owner-reported live receipts; B60 did not
repeat the exercise or directly inspect its protected receipt.

## What passed and what did not

The one approved prepare-only exercise reports healthy durable `PREPARED`,
an inert healthy watchdog path, owner-loss detection and nested recovery
`cancelled-prepared`. It issued zero consumer commands and no model call;
postchecks left no lease/runtime artifacts, preserved production and left F2
and F6 unchanged. The protected receipt SHA-256 is
`d5cad1d3627da55ccb3ae58318105a05791aa653ac77a26984897ef2e060be13`.

This is meaningful pre-effect recovery proof, not measured recovery after
consumer stops, model replacement or a GPU failure. Production F6 remains
disabled/inactive. F2–F5 and the exact effectful card/approval still gate it.
The October 26 F2 attempt is independently owned; do not change or replay it.

## B60 integration response / gaps to preserve

The new two-phase ordering and durable admission digest are appropriate for
review: bind same-cycle source receipts, lease ID/generation and exact workload
identities before `PREPARED`, persist them through every phase, and enter
recovery after any post-validation failure once consumer effects begin.
Never invent extra acquire fields or pass unvalidated caller-selected paths.
The fixed F4/F5 producer and consumer are still a proposal, not installed
admission. Request the implemented producer/controller source and exact
source-bound tests when published; the owning platform ref is still older.

The currently proposed evaluation lease freezes D4 candidate-H plus M3 NLU
on accepted 9B/SYCL. It is not yet a general B60 challenger lease or the A1
full-Aster-path benchmark. Candidate-G's approval does not transfer to H;
neither workload approval transfers to 27B+ or a runtime replacement. The
dedicated unprivileged D4 descriptor path and fixed M3 source-local key-file
path remain distinct; do not copy a credential or silently unify them.

Prepare the later B60 integration explicitly: a reviewed candidate manifest,
accepted-control recovery, GPU/resource/consumer gates, model/runtime switch
boundary and full-path gateway observation must be bound to the same lease.
No tool or policy grant follows. Current 9B-only identities cannot simply be
relabelled as a challenger, and direct D4/M3 endpoint timing is not A1 usable-
answer latency. Preserve 30-minute B60 trials and restoration before 04:15;
the D4 service's longer maximum and a proposed 90-minute lease do not extend
B60's existing experiment envelope. This identifies a future interface gap,
not permission to implement or activate a competing controller.

## Local continuation

Eight existing offline peer-admission/recovery-margin tests pass; Git object
connectivity passes. They are not tests of the newer unpublished platform
implementation or a live recovery measurement. No production probe, model,
GPU, scanner, consumer, timer, lease, credential, mount, download or package
action occurred. No push in this nightly turn. Retain this receipt for the
next authorized liaison continuation, then consume actual F2 terminal evidence
and implemented admission source without duplicate execution.
