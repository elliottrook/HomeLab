# M3 NLU candidate-bundle boundary — 2026-10-25

> Status: offline custody boundary; no candidate selected and no authority

## Gap

The threshold policy, calibration release and shadow release all carried a
`candidate_bundle_sha256`, but no Stream A schema established what an NLU
candidate bundle had to contain. A digest-shaped value could therefore satisfy
those individual schemas without proving that the intended engine and its
supporting policy, contract, adapter and runtime profile were frozen together.

## Boundary

The new content-free `aster-nlu-candidate-bundle.v1` template and validator pin:

- candidate identity and engine class;
- exact engine, interpretation policy, contract, adapter and runtime-profile
  digests;
- matching none/local/cloud egress semantics;
- disabled tools, absence of case data and literal `authority: not-granted`;
  and
- a canonical bundle digest.

A separate binding check requires a registered or frozen threshold policy to
name the SHA-256 of the exact sealed candidate bytes. Duplicate keys, component
drift, mismatched engine/egress classes, case-data claims and authority claims
fail closed.

## Verification and effect

The focused NLU suite passed **60/60** tests with the bundled workspace Python
runtime on 2026-10-25. The work was offline and did not select a candidate,
create calibration cases, inspect a holdout, call a model or alter live routing.

The next calibration dependency is now explicit: select and seal one exact
candidate bundle, then create the independently custodied calibration release
before registering the accepted numeric policy. Automatic routing remains off.
