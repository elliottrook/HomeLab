# SA1/SA2 source boundary and presentation candidate

Date: 2026-09-28
Status: **reviewable local design and fixture-only presentation; not deployed**

## Proposed first producer boundary

The first connected candidate, if separately accepted, is one source-local
`aster-gateway-status/v1` producer. It would observe only the Aster gateway's
fixed status fields and write a strict version-1 envelope to a local,
root-controlled handoff. It would not receive a general administrator identity,
an API key, model prompts or a network target supplied by chat. The Aster
gateway would consume only that handoff through an individually disableable
adapter configuration.

Before connection, the deployment review must name the actual service identity,
handoff owner/mode, exact selected fields, freshness limit, record retention,
maximum read rate, per-source disable control and failure behavior. Failure must
produce `unavailable` evidence; it must not retry indefinitely, broaden access
or substitute stale success. This document intentionally does not invent those
live configuration values.

## Fixture-only presentation

`sysadmin_incident_stream.py` turns the persisted incident state into three
deterministic server-sent-event frames: a reconnect progress event, a concise
incident event and `[DONE]`. The incident presentation contains provenance,
age, state, truncation and summary for each observation, plus the next proposed
read-only check. It intentionally excludes evidence facts, hypotheses, prompts,
model reasoning and raw producer records.

The module does not add a FastAPI route, authentication change, service unit or
source adapter. It is a tested serialization contract for a later authenticated
route to relay.

## Validation and limits

Two presentation tests confirm ordered frames, reconnect age and next-step
content, and confirm that facts and hypotheses never reach the presentation.
Together with the nine producer/persistence tests and seven existing evaluation
harness tests, this validates only local contracts. It does not establish SA1 or
SA2 completion, Qwen capability, streaming in the running Aster gateway, or any
live diagnostic access.
