# SA2 Doctor-status registered producer boundary — 2026-10-27

## Result

The SA2 registry now has a source-only third read-only producer for the already
registered `homelab-doctor/status` pair. It reuses the existing fixed Doctor
adapter and reads only `/var/lib/aster/health/latest.json`. It cannot refresh
Doctor, select another path, invoke a command, contact a network target, call a
model or perform a repair.

The caller still supplies only an incident identity. The pending, state-bound
SA1 journal decision selects the target and kind. The executor has no path
parameter and the HTTP request surface has no path field. Tests replace the
module's fixed path without widening the operational function signature.

The producer copies only the adapter's validated observation contract into the
strict producer envelope. A valid report yields status, age, check count and a
truncated report digest. Check names and summaries are not copied. Missing,
stale, malformed, oversized, writable or linked reports remain bounded
`unavailable` evidence instead of becoming a guessed result.

## Exact source

- `sysadmin_registered_producer.py` SHA-256:
  `3291feaaace83a42f98f578f29e0b2831a82c8b1cae31793a0cdb0b4a622353a`;
- `test_sysadmin_registered_producer.py` SHA-256:
  `cf63686d23edb5b898630f4adaba7d271ff9f6b13d2ebc710121fb99546b8147`;
- reused `doctor_incident_adapter.py` SHA-256:
  `0baece59b29dcee47395dbc42bab742ba33fa0d3ad708ffedc41c22a2ae23968`;
- strengthened `sysadmin_incident_store.py` SHA-256:
  `5676b4b865b5ff9100802967dbce1a455aa6a4d8815ac0e489dc09e368978328`.

## Validation

- focused producer/Doctor/store/follow-up suite: **29/29 passed**;
- complete dependency-free `test_sysadmin*.py` suite: **72/72 passed**;
- the new cases prove successful fixed-report ingestion, content minimization,
  pending-decision consumption, bounded unavailable behavior and rejection if
  the pending decision changes while its producer runs;
- duplicate JSON keys in the Doctor report now fail closed.

## Boundary and next gate

No live file, route, database, service, schedule, model or authority changed.
This source is not included in the candidate-E four-file installer. It should
be independently reviewed and target-runtime tested as a later SA2 release
candidate after the candidate-E gateway installation is reconciled. A later
deployment would require its own exact card and Aster Agent restart approval.

