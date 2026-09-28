# SA1/SA2 incident retention and quota candidate

Date: 2026-09-28
Status: **local implementation candidate; not deployed**

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
count-limit denial and storage-limit denial. This is not deployed on LXC 104;
the existing adapter remains disabled and its prior canary state was removed.

## Next gate

The retention prerequisite is now represented in source but needs a separate
review/deployment decision. A future real authenticated-Companion pilot must
deploy this exact version, verify state-directory owner/mode and bounded-database
behavior as the `aster` service user, then validate one real session's incident
creation and reconnect stream. It must retain the feature-disable rollback and
must not add any target, model change, repair path or collector refresh.
