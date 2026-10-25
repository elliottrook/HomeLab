# M3 NLU holdout artifact-binding boundary — 2026-10-25

## Problem

The content-free holdout manifest carried SHA-256 fields for the frozen
interpretation contract, scorer, threshold policy and development-set
non-overlap receipt. Its bundle validator independently read and checked only
the threshold-policy bytes. A manifest with syntactically valid but unrelated
contract, scorer or non-overlap digests could therefore pass bundle validation.

## Correction

A sealed holdout bundle must now supply the exact bytes for all four claimed
artifacts. The validator hashes each input and compares it to its named manifest
field before accepting the bundle. Threshold-policy semantic validation and the
requirement for a frozen policy remain unchanged.

## Validation

The focused NLU suite passes **48/48** under the bundled Python environment.
The new cases independently drift the contract, scorer and development
non-overlap receipt bytes and verify that each mismatch fails closed. Existing
threshold-policy drift and template-policy rejection continue to pass.

This is an offline custody correction. It creates no holdout cases or labels,
reads no private content, registers no numeric policy, runs no classifier,
enables no route or egress, and grants no authority.
