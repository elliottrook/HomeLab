# SA1/SA2 incident retention and quota candidate

Date: 2026-09-28
Status: **installed disabled on LXC 104; no authenticated pilot run**

## Boundaries

`IncidentStore` now has fixed defaults for a future enabled pilot:

| Control | Value | Behavior |
|---|---:|---|
| Retention | 24 hours | Expired incidents are deleted before writes and reconnect reads |
| Incident count | 8 | A ninth distinct incident is rejected before persistence |
| Database size | 256 KiB | A write that would exceed the reserved SQLite size bound is rejected before persistence |

These caps apply to the small sanitized incident record only. They do not retain
raw Doctor output, credentials, prompts or reasoning. SQLite's page allocation
is variable, so the storage check reserves 8 KiB before each write rather than
allowing a record to cross the stated limit.

## Validation

Sixteen local tests pass across the incident, producer/store, presentation and
Doctor adapter contracts. New tests prove expiry before a later write/reconnect,
count-limit denial and storage-limit denial. The published store was then
installed on LXC 104 with the prior file retained in the existing rollback
directory. Its deployed SHA-256 is
`4e8a36a803c3d8e5eac362e4c17a0cadc1f4ae2accca05cc73283b646b8e5c4b`, matching
source. `aster-agent` restarted active, its health response remained normal and
the Doctor adapter was confirmed disabled. No state or authenticated pilot ran.

## Next gate

The retention prerequisite is now deployed but remains inactive with the
adapter. A future real authenticated-Companion pilot must verify
state-directory owner/mode and bounded-database
behavior as the `aster` service user, then validate one real session's incident
creation and reconnect stream. It must retain the feature-disable rollback and
must not add any target, model change, repair path or collector refresh.
