# A1 source-bound recovery-window contract — 2026-10-18

**Status:** offline platform contract only; live A1 remains blocked. No host
file, lease, watchdog, model, or production service was touched.

## Completed boundary

The platform-owned `ApplicationReceipt` now carries two distinct fields:

- `restore_start_epoch`: the watchdog recovery trigger;
- `restore_deadline_epoch`: the hard completion deadline.

`from_lease_receipt()` receives both values explicitly from the persisted
application state. The receipt validator rejects non-integer or non-increasing
windows and receipts past the hard deadline. The active-admission projection
requires both fields to match the current armed state, lease identity and
generation; it includes both fields in the content-free admission payload.
This prevents the former ambiguous mapping of `watchdog_deadline_epoch` from
being treated as a recovery trigger.

## Evidence

- Changed source: `scripts/local-ai/application_receipt_boundary.py` and
  `scripts/local-ai/application_b60_controller.py`.
- Focused application tests: 63 passed.
- Complete `scripts/local-ai` suite: 212 passed, 4 expected macOS
  root-custody skips.
- Tests cover invalid/past windows and a receipt window mismatched to current
  persisted state. A current admission is accepted at
  `restore_start_epoch - 1` and rejected at the exact trigger and afterward;
  renewal uses the same current-boundary loader.

## Remaining gates

This is not a source-authenticated pre-lease producer or live admission. The
platform still needs a fixed host callback that obtains current lease, lock,
backup and watchdog evidence itself; measured worst-case restoration and
timer/observer lag; target-Linux custody/import proof; and a separately
approved bounded application-only drill. The A1 checker must consume this
projection without treating the hard deadline as the trigger.
