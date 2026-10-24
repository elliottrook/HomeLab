# M3 NLU development scorer — 2026-10-24

## Result

The explicit NLU boundary now has a pinned, content-safe development benchmark.
The exposed synthetic fixture contains 24 cases, four for each
`request-interpretation.v1` family. It includes personal, mixed-intent,
ambiguous, denied and unsupported examples. Its SHA-256 is
`1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`.

The independent scorer reports these dimensions separately:

- request family;
- sensitivity;
- capability needs;
- ambiguity;
- disposition; and
- reason.

It additionally reports privacy underclassification, privacy
overclassification, unsafe false routing, unnecessary non-routing, missing and
extra capability cases, per-family completeness and bounded latency. Missing,
invalid and failed attempts remain in the denominator. Runner totals are
recomputed rather than trusted.

## Safety boundary

Run records and score output contain no request text. The scorer accepts only a
strict `request-interpretation.v1` record bound to the manifest's principal,
engine digest and policy digest. Extra prompt, entity, confidence or authority
fields fail validation. Invalid attempts may retain only bounded error classes;
they cannot carry an interpretation.

The benchmark disables tools and execution. It records engine locality but does
not select a provider, grant egress, issue a route proposal or project an AI-PAM
capability. A cloud engine must declare cloud egress in its evidence manifest;
this is disclosure, not permission.

## Validation

Using Python 3.12.14 and Pydantic 2.14.1:

- the new scorer suite passed 10/10;
- the focused NLU, route, Decision and Outcome semantic suites passed 11/11;
- combined focused result: 21/21.

The historical full adapter suite was not repinned. Its reviewed-source drift
continues to fail closed, as previously documented.

## Limit

These cases and labels are developer-visible and authored with the scorer. They
are regression evidence only. They do not estimate real request accuracy,
calibrate abstention, establish a safe cloud route or authorize automatic
handover. The accepted human-label protocol, independent holdout, frozen
calibration, no-effect shadow comparison and promote-or-reject review remain
open.

