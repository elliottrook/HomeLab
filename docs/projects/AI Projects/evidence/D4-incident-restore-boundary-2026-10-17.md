# D4 persisted incident restore boundary — offline check

**Scope:** source-only incident evidence contract. No connected Codex tool,
credential, host access or model call.

The investigation component could raise a generic Python exception when a
persisted plan or observation had the wrong shape. It also accepted an
unvalidated clock argument until timestamp subtraction, where a naive clock
could fail outside the component's controlled error contract. These are
recovery-path input failures, not evidence of malformed production records.

The candidate now requires an aware clock and validates each persisted plan
and observation shape before reconstructing the incident. A damaged row fails
with `InvestigationError`; it is not silently repaired, executed or presented
as a valid observation. The normal saved-record round trip still succeeds.

The focused investigation, incident-store, incident-stream and Doctor model
projection suite passed **30/30** locally. This is an offline contract result.
It does not authenticate an evidence producer, grant read-only tools, establish
diagnostic usefulness, or advance M1 Stage 2 / D4 connected-tool release.
