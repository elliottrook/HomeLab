# D4 fixed Aster Speech projection — offline candidate

**Date:** 2026-10-26  
**State:** source-only candidate; no live reader, caller or grant

## Candidate

The first schema-3 consumer is fixed to `aster.speech`.
`speech_catalogue_incident_adapter.py` opens the aggregate and catalogue with
`O_NOFOLLOW`, requires the configured owner, regular one-link files, restricted
permissions and bounded sizes, and validates:

- exact schema-1 and schema-3 shapes with duplicate JSON keys rejected;
- equal generation time and exact aggregate SHA-256 binding;
- a valid catalogue run ID and unique bounded check list;
- presence of exactly the named `aster.speech` selection;
- source/aggregate severity consistency; and
- a UTC observation no more than 36 hours old and not in the future.

Any failed or uncertain condition returns a deterministic `unavailable`
observation with no facts. A valid state exposes only the fixed check ID and a
truncated report digest; aggregate summaries and speech-probe output never
enter the observation.

`fixed_speech_response.py` accepts only that source, named fact, state,
timestamp and bounded age. Its deterministic answer states the named status,
freshness and scope, and explicitly says the result cannot identify a failing
speech component, authorize repair or establish wider system health.

The offline investigation policy now registers only `status` observations for
the exact `aster-speech` target. This is a type-level boundary, not a caller,
credential, grant or route.

## Validation

- focused catalogue, speech adapter/response and investigation tests:
  **24/24 passed**;
- combined new and existing fixed-Doctor boundary tests: **46/46 passed**;
- Python compilation: passed.

Coverage includes pass/warn/fail/unavailable mapping, private-summary
exclusion, missing fixed check, unknown catalogue entries, digest/time/schema
drift, duplicate fields, severity contradiction, stale/future time, unsafe
permissions, symlink and hard-link custody, response-field drift and the full
36-hour source freshness boundary.

## Boundary and next step

No production file or process changed. No gateway imports this adapter, and no
identity, capability, grant, model route, model call, repair or automatic
routing exists for it.

The next source milestone is an exact empty-request fixed speech gateway and a
dedicated caller boundary that returns only the deterministic response with
authority `not-granted`. It must remain separate from the existing fixed
inference capability and from generic shell or repair access.
