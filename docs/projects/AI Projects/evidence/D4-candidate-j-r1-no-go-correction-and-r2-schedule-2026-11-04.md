# D4 candidate-j R1 NO-GO, correction and R2 schedule — 2026-11-04

R1 claimed exactly at 21:00 and ended terminal NO-GO at 21:03:07 with
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and production restored. No
model request ran. The wrapper incorrectly rejected expected inert
candidate-g/i packet files in the shared runtime directory before transport.

The bounded correction removes only those two predecessor packet names from
the existence ban. Review/decision material remains forbidden, candidate-j's
five-file pins remain isolated, and automatic routing/authority remain off.
The corrected wrapper installed inactive on host and guest at `a883c144…5f2a`.
The installation preserved the concurrent EPUB alignment additions in the
41-pin release manifest, restarted no service and left the lease ready with no
state or locks.

The ledger rejected 22:00 because AsterTV alignment owns 22:15–22:45 plus
recovery through 23:00. Fresh booking
`aster-stream-a-sa3-candidate-j-20261104-2300-r2` therefore uses the first
complete clear window, 23:00–23:45 (`-07:00`). R2 remains conditional on all
fresh runtime gates and must produce six valid rows, exactly two model requests,
zero retries/errors/effects and complete production restoration.

## R2 terminal result and deterministic correction

R2 claimed exactly at `2026-11-04 23:00:00 -07:00` and ended terminal
NO-GO at `23:03:46` after 226 seconds. Root-custodied terminal evidence records
`first_failure_phase=owner-transaction`,
`failure_code=OWNER_TRANSACTION_FAILED_RESTORED` and
`production_restored=true`. The bounded owner error is `candidate-j listener
exited nonzero: candidate-j result identity or count invalid`. R2 is spent and
must not be retried.

Independent source reconciliation identified a deterministic identity-contract
defect. The public fixture's raw file bytes have SHA-256
`40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f`,
which correctly protects installed-file custody. The batch result intentionally
identifies the fixture's canonical semantic JSON, whose SHA-256 is
`cb94f6ea576aafa7710b72e8711510864eb0026f39f14d53f100f3c470ae8e85`.
The wrapper and transaction incorrectly required the raw-file digest in the
result field, so they rejected the otherwise correctly identified result.

The source correction now names and enforces both invariants separately:
`FIXTURE_FILE_SHA256` remains the custody pin and
`FIXTURE_SEMANTIC_SHA256` is the only accepted result identity. Regression
tests prove the values differ and reject the raw digest when presented as
semantic identity. The focused platform suite passes 60/60 and candidate-j's
source suite remains 17/17. A dedicated inactive installer preserves the
concurrent 41-pin EPUB release manifest, changes only the host wrapper,
transaction and derived manifest plus the guest wrapper, retains a new
root-only rollback checkpoint, and performs no restart or model request.

The correction subsequently installed inactive from mirrored platform commit
`816791af`. Independent postchecks accepted identical host/guest wrapper
`fc283224…06f4`, host transaction `c2fbcf6b…4108`, derived concurrent 41-pin
manifest `99e41a1e…9fda`, unchanged EPUB pins, ready lease, absent locks/state,
running LXC104/110/116 and healthy Aster Agent, accepted llama.cpp/SYCL,
Speech, `pvescheduler` and `pvestatd`. The installation restarted no service
and invoked no workload. The temporary install stages were removed and the
root-only rollback checkpoint was retained.

The authoritative ledger then rejected 04:00 because the protected daily B60
reservation at 03:10–03:55 retains a 15-minute recovery reserve. It returned
clear for the complete 04:15–05:00 PST window. Distinct booking
`aster-stream-a-sa3-candidate-j-20261105-0415-r3` is scheduled there with the
registered fixed workload. R3 remains conditional on every fresh claim-time
ledger, hash/custody, lease, lock, conflict and production-health gate. It may
run once only and grants no retry, routing, authority or promotion.
