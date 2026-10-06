# SA3 Doctor read-only pilot plan

Status: **prepared; adapter pilot not launched; related existing Doctor job observed**

## Scope

One existing authenticated user request opens one Doctor incident through the
already deployed Aster adapter. The adapter may read only the fixed Doctor
report path, create a bounded local incident record, and present provenance,
freshness, state, and the proposed next read-only observation. No model,
credential, network target, configuration, restart, remediation, or background
schedule is enabled.

## Preconditions

- live hashes of `doctor_incident_adapter.py`, `sysadmin_investigation.py`, and
  `sysadmin_incident_store.py` match reviewed source;
- Aster, broker, approval bridge, and Doctor path are healthy;
- a fresh user authenticated request is available;
- retention remains 24 hours, at most eight incidents, and 256 KiB.

## Acceptance evidence

- a new incident has one fresh, non-duplicated Doctor observation;
- it contains no secret-shaped field or production effect;
- reconnect/presentation exposes only the safe public shape;
- repeated request follows dedup/cooldown behavior;
- disablement is verified after observation.

## Observed execution — 2026-10-03

Jason sent one authenticated Doctor request through Aster. It did **not** reach
this adapter: `ASTER_SYSADMIN_DOCTOR_EVIDENCE` was disabled on the live Aster
runtime. The request instead used the separately deployed Lab Operations Doctor
workflow.

That workflow claimed one fixed-script job and performed no remediation, but
ended `unknown` with code `interrupted`, `coverage: none`, and zero recorded
checks. Its pending record had no result, which proves only that the worker was
interrupted before result delivery. The private operation log also lacked the
final `Passed`, `Warnings`, and `Failed` summary markers. This is a separate
incomplete-output observation, not proof of the interruption's cause. No retry
was initiated.

This is evidence of a contract mismatch between the fixed Doctor script output
and Lab Operations result parser. It is **not** evidence that the lab is
healthy, unhealthy, or that this incident adapter satisfies its acceptance
criteria. The adapter pilot remains unlaunched and cannot be promoted from this
observation.

## Stop and rollback

Stop on stale/oversized/sanitization-failed evidence, broker/identity failure,
unexpected target, or any attempted effect. Disable the incident path, retain
only the bounded evidence record, and make no retry until reviewed.

## Approval boundary

Launching the pilot is a live authenticated read and requires explicit
immediately-before-launch authorization. This plan does not grant it.
