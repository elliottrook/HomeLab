# M3 NLU shadow artifact-binding boundary — 2026-10-25

## Problem

The no-effect shadow manifest recorded an interpretation and route-proposal
digest for each opaque case, but bundle validation checked only the frozen
threshold policy and candidate. Digest-shaped interpretation/proposal claims
were not tied to supplied artifacts.

## Correction

A sealed shadow bundle must now provide exactly one content-free interpretation
and proposal artifact for every manifest case and no extra cases. Their exact
bytes are hashed and compared with the per-case fields. Missing, extra,
malformed or drifted artifacts fail closed. Existing S0-only, no execution,
no provider egress, frozen-policy and candidate boundaries remain unchanged.

## Validation

The focused NLU suite passes **52/52** under the bundled Python environment.
New tests reject an incomplete artifact set and a drifted proposal while the
fully bound control passes.

This is an offline evidence-custody correction. It collects no live shadow
traffic, reads no request text, invokes no provider, changes no route and grants
no authority.
