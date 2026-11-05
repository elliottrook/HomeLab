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
