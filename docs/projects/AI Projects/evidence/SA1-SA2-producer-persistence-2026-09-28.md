# SA1/SA2 producer and persistence checkpoint

Date: 2026-09-28
Status: **local candidate; no gateway deployment or live producer**

## Delivered contract

The offline incident component now has two supporting artifacts:

- `sysadmin_incident_store.py` accepts only a version-1, exact-field,
  source-local producer envelope and persists the validated incident record in
  local SQLite.
- `evals/sysadmin-producer-fixture.json` is a credential-free status fixture
  for the Aster gateway. It contains no endpoint, user data, command or secret.

The producer name is versioned and constrained; the envelope binds the producer,
its production time and one exact-shape observation. Unknown fields, unsupported
versions, invalid producer names and future timestamps are rejected. The nested
observation remains subject to the registered target/kind, provenance, age,
truncation, size and secret-shaped-field rules.

The SQLite record stores the incident plan, observations, hypotheses and plan
cursor, not model prompts or a transcript. On reconnect, `reconnect_snapshot()`
rehydrates and revalidates the complete record, recalculates observation age and
returns a versioned `aster.incident` snapshot. A malformed persisted record fails
closed.

## Validation

`python3 -m unittest test_sysadmin_investigation.py test_sysadmin_incident_store.py`
passes nine local tests. They cover the original evidence contract plus fixture
ingestion, process-reopen/reconnect state, producer-envelope denials, tampered
stored state and duplicate delivery denial. The initial reconnect test exposed
that restored evidence age was being recalculated at the observation time; the
store now receives the reconnect time and recalculates it correctly.

## Limits and next action

This stores only local test state. It is not configured in `aster-agent`, has no
endpoint, does not emit server-sent events, and does not run an adapter against
a guest, Forgejo, a network device or a backup source. No live target, service,
credential, Qwen setting or tool authority changed.

Before connecting even one source, review an individually disableable producer
boundary: exact service account, source-local sanitization fields, file/socket
transport, retention, freshness timeout, load limit and failure mode. Add an
SSE/Companion presentation only after that state contract is accepted; it must
show progress/evidence summaries without model reasoning or raw records.
