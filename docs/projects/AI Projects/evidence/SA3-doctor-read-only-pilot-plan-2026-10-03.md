# SA3 Doctor read-only pilot plan

Status: **prepared; not launched**

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

## Stop and rollback

Stop on stale/oversized/sanitization-failed evidence, broker/identity failure,
unexpected target, or any attempted effect. Disable the incident path, retain
only the bounded evidence record, and make no retry until reviewed.

## Approval boundary

Launching the pilot is a live authenticated read and requires explicit
immediately-before-launch authorization. This plan does not grant it.
