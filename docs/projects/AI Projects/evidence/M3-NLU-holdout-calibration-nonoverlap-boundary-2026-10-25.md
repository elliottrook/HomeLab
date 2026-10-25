# M3 NLU holdout calibration non-overlap boundary — 2026-10-25

## Problem

The original content-free holdout release bound a development-set non-overlap
receipt, but no calibration set existed when that contract was written. After
the 60-case calibration set was sealed, the unchanged schema could admit a
future holdout that excluded development cases yet reused calibration text.
That leakage would invalidate independent qualification.

## Correction

A sealed holdout manifest must now carry a separate
`calibration_nonoverlap_receipt_sha256`. Bundle validation requires the exact
receipt bytes and verifies their digest independently from the existing
development non-overlap receipt. Both receipts must pass the new fixed semantic
schema: exact reference artifact and normalized-set pins, 36-case common
subject, zero overlap, an independent non-overlap reviewer, self-hash and no
authority. The two receipts must describe the same holdout source and text set.
The template leaves both fields empty and cannot claim either proof.

The future holdout custodian must take the sealed calibration normalized-text-
set SHA-256
`c5b555b806a1cf57c35797bd97d8c691c5258593f7783a46b4e45041e39e12e3`
as an exclusion input. The receipt format and custody process must prove zero
normalized overlap without placing request text in Git.

## Validation and effect

The 16 focused receipt/holdout tests pass, including unique-key parsing,
reference drift, nonzero overlap, authority and mismatched-subject failures.
The full dependency-free NLU suite passes 96/96.
No holdout case or label was created or opened; no model ran; no threshold,
shadow route, deployment, tool or authority was granted.
