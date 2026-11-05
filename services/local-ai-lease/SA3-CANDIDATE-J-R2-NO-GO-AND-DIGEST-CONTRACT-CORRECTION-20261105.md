# SA3 candidate-j R2 NO-GO and digest-contract correction — 2026-11-05

Booking `aster-stream-a-sa3-candidate-j-20261104-2300-r2` claimed exactly at
23:00 PDT and ended terminal NO-GO at 23:03:46 after 226 seconds. The retained
terminal reports `owner-transaction`, `OWNER_TRANSACTION_FAILED_RESTORED` and
`production_restored=true`. The bounded owner error is `candidate-j listener
exited nonzero: candidate-j result identity or count invalid`. R2 is spent and
is not eligible for retry.

The failure is a deterministic contract mismatch, not a model-quality result.
The installed public fixture file is correctly custody-pinned by raw-byte
SHA-256 `40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f`.
The public scorer and batch intentionally identify its canonical semantic JSON
as `cb94f6ea576aafa7710b72e8711510864eb0026f39f14d53f100f3c470ae8e85`.
The guest wrapper and host transaction incorrectly compared the result's
semantic identity with the raw-byte custody digest.

The correction gives the two values separate names and purposes. Runtime pin
checking continues to require the raw file hash; result validation now requires
only the canonical semantic hash. Regression tests prove the values differ and
that substituting the file hash into the result is rejected. The focused
candidate-j, reservation and runtime suite passes 60/60.

The dedicated inactive installer requires the exact installed R2 baseline:

- wrapper `a883c144…5f2a` -> `fc283224…06f4`;
- transaction `a7a1ccc8…5ab` -> `c2fbcf6b…4108`;
- installed concurrent 41-pin manifest `1f048141…c845` -> derived
  `99e41a1e…9fda`;
- guest wrapper changes identically to the host wrapper.

It requires and preserves the two concurrent EPUB pins, changes no other
manifest entry, retains a distinct root-only rollback checkpoint, requires a
ready lease with absent shared state/locks and refuses an active candidate-j
unit. It does not restart a service, call a model, create a booking or infer
promotion.

## Inactive installation result

The correction installed successfully from platform commit `816791af` with no
booking, workload effect, model request or service restart. The retained
root-only checkpoint is
`/var/lib/local-ai-lab/checkpoints/sa3-candidate-j-digest-r2-20261105`.
Independent postchecks accepted:

- host and guest wrapper `fc283224…06f4`;
- host transaction `c2fbcf6b…4108`;
- derived 41-pin installed manifest `99e41a1e…9fda`;
- unchanged EPUB adapter `59d47d79…af8c` and transaction `fb4cbcb5…a50`;
- ready lease and absent lease/shared-operation state and locks;
- running LXC104/110/116, active Aster Agent, accepted llama.cpp/SYCL and
  Speech, plus active `pvescheduler` and `pvestatd`.

The bounded temporary host and local stages were removed after verification;
the rollback checkpoint remains. A new transaction requires its own distinct
ledger booking and all fresh claim-time gates. R2 remains spent.

## R3 exact booking

The authoritative ledger showed the daily protected B60 reservation at
03:10–03:55 PST and rejected 04:00 because its recovery reserve still
overlapped. The complete 04:15–05:00 window returned `clear`. Distinct booking
`aster-stream-a-sa3-candidate-j-20261105-0415-r3` is now scheduled for that
exact window with the registered, hash-pinned
`sa3-evidence-matrix-candidate-j-public-v1` workload.

R3 remains conditional on immediate claim-time ledger recheck, exact installed
hashes/custody, ready whole-host lease, acquired shared operation lock, absent
competing work and healthy production. It may run once only. Failure or
uncertainty retains evidence and restores production without retry; completion
grants no routing, authority or promotion.
