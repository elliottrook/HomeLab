# M3 NLU calibration candidate binding — 2026-10-25

> Status: offline admission correction; no calibration or routing authority

## Finding and correction

The calibration bundle validator previously proved that a sealed release and a
registered policy named the same candidate digest, but it did not receive the
candidate bytes. Two matching digest-shaped claims were therefore insufficient
to prove that a valid Stream A candidate had actually been sealed.

Calibration bundle validation now requires the exact candidate manifest. It
validates the candidate's schema and canonical self-digest, requires sealed
status, and verifies that the policy's `candidate_bundle_sha256` matches the
SHA-256 of those exact bytes. The existing release-to-policy candidate check
then closes the three-way binding among candidate, registered policy and sealed
calibration release.

## Verification and effect

The focused NLU suite passed **61/61** tests with the bundled workspace Python
runtime on 2026-10-25, including exact-candidate drift rejection. No candidate
was selected, no calibration evidence was created or inspected, and no model,
provider, tool or live route was used.

Automatic routing remains off. The next operational inputs remain one selected
and sealed candidate plus an independently custodied calibration release.
