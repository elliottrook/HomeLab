# SA1 follow-up selection boundary — 2026-10-26

## Result

**SOURCE-ONLY BOUNDARY PASS.** `sysadmin_followup_selector.py` adds the missing
decision boundary between a model or human hypothesis and a read-only
observation request. It accepts one exact-shape proposal bound to the SHA-256 of
the complete current incident record. A stale proposal or a proposal for
another incident fails closed.

An `observe` decision can select only an unfilled target/kind pair already in
the incident's preregistered plan. It may choose a later unfilled pair when that
check better discriminates the current hypothesis, which supplies bounded
adaptive follow-up without allowing target discovery. The returned request
uses the registered reason and states `execution: not performed`.

`complete` and `escalate` decisions contain no request and make no success
claim. Every decision carries literal `authority: none` and `effect: none`.
The returned incident reference is a bounded digest rather than the arbitrary
internal incident identifier.

## Validation and remaining boundary

Seven focused tests cover adaptive selection within the plan, already-filled
and unplanned denial, stale/cross-incident denial, exact schema and bounds,
terminal no-effect behavior, and state-digest changes after evidence or
hypothesis changes. The existing investigation/store/stream suites remain
separate regressions.

This module has no network, subprocess, filesystem-discovery, credential,
producer or service integration and is not deployed. The incident store now
adds the missing atomic journal boundary: one pending decision survives process
reconnect, a second decision is denied, and only a producer envelope matching
the selected target/kind can consume it. A changed incident record makes the
pending decision stale and fails closed. Consumed decisions remain in the
bounded incident database until that incident expires, preserving the concise
hypothesis and selection history without a transcript.

Three store integration regressions cover reconnect/consume, duplicate and
mismatched denial, and stale-state denial. The reconnect presentation is now
schema v3 and exposes only decision/consumed counts plus a hashed pending
decision reference, disposition and registered target/kind. It excludes the
hypothesis summary, internal incident identifier and raw journal record;
malformed or unregistered presentation state fails closed.

A complete source-only flow fixture now selects a later gateway-log check,
survives a process reconnect, consumes only its matching envelope, revises the
hypothesis, selects an inference-status check, records its unavailable result,
and finishes with an explicit escalation. Two consumed decisions and one
terminal pending decision remain in the bounded journal, while the incident
snapshot retains exactly two observations. The combined target-environment
suite passes **50/50** with `ResourceWarning` promoted to an error. The
source-only gateway route now accepts the opaque state digest and proposal only
through the existing authenticated owner boundary. The legacy API key is
denied, stale state returns a fixed conflict without adding a journal row, and
the response/stream never echo the private hypothesis. The route only journals
the proposal; it cannot run the selected observation. A later SA2 effect gate
must still register and deploy each actual observation source.
