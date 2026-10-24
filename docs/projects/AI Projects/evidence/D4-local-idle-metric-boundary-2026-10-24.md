# D4 local idle-metric boundary — 2026-10-24

**Scope:** offline hardening of the future label-free D4 evaluation executor.
No private holdout, credential, network service, model or live route was used.

## Finding

The executor's readiness check accepted any number of matching Prometheus
`requests_processing` series and relied on Python truthiness after converting
their values to floats. That was fail-closed for most malformed or busy
responses, but it left duplicate-series semantics implicit and did not state a
finite, nonnegative gauge boundary.

## Correction and evidence

The executor now requires exactly one matching requests-processing series. Its
value must parse as a finite, nonnegative number, and only exactly zero is idle.
Missing, duplicate, negative, `NaN`, infinity and nonnumeric synthetic metrics
are rejected. The normal labelled zero gauge passes.

The complete evaluation suite passes **123/123**.

## Decision

This makes the future local-service admission check deterministic and
fail-closed. It does not verify the production metric shape, execute the
holdout, qualify a model, connect a tool or advance D4/M1.
