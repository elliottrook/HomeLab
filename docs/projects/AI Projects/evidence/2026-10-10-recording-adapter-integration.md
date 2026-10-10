# Aster recording-adapter integration

Date: 2026-10-10

Status: **offline integration gate passed; connected provider capture and repeat
9B session remain pending**

## Result

The target-architecture candidate now has a provider/entity registry boundary
that cannot perform effects. A caller supplies a sanitized, versioned snapshot;
the deterministic planner may emit only one of four allowlisted capabilities;
and the adapter validates the exact argument schema and registry binding before
recording an event with `effect_permitted: false`.

The adapter contains no network client, Home Assistant token, media-provider
handle or timer implementation. Unknown capabilities, stale snapshot schemas,
duplicate registry names, unknown entities/targets, malformed arguments and a
breached call limit fail closed before a record is accepted.

## Independent corpus

`aster-recording-adapter-v1.json` is a second, independently authored sealed
synthetic corpus. Its 14 cases cover integer and decimal timers, conflicting and
missing durations, exact and unknown timer cancellation, bound and missing
media targets, exact and unknown entities, ambiguous/unsupported alarms and a
non-household analysis request.

The corpus runner produced:

- 14/14 accepted expectations;
- zero permitted effects;
- corpus canonical SHA-256
  `142368a5760a02cbe69b6db602c7a765a40b4ffd3b1a748ace94691cda32ed86`;
- report SHA-256
  `03e7662ec8805400db1bbfbecdb649ec7a1632a1ac0a67aec2898370fe7ae4bc`.

The output path uses exclusive creation so an existing evidence result cannot
be overwritten accidentally.

## Regression evidence

- 16/16 focused orchestrator tests pass.
- 72/72 evaluator tests pass.
- Six focused corpus/grounding runner tests pass.
- The wider service import set remains partially unavailable on the local Mac
  because optional `PyJWT` and `FastAPI` dependencies are not installed. This
  is the same environmental limitation recorded by the preceding evaluation;
  no package installation was performed and it is not counted as a pass.

## Boundary and next gate

This proves fixture registry behavior, schema/version telemetry and absence of
an effect path. It does not prove that a live provider/entity registry can be
captured correctly, that the 9B model repeats its grounded result in a separate
session, or that production traffic can use the boundary.

Next, capture only sanitized names/availability from the real registries through
their existing read-only paths and replay that snapshot into this adapter. Then
run the second independent grounded-analysis corpus against a temporary 9B
reasoning-off endpoint. No effectful adapter, production endpoint, persistent
configuration or model promotion is authorized by this result.

## Continuation attempt

A distinct sealed v3 grounded-analysis corpus was prepared with twelve new
synthetic cases. It covers household follow-ups, non-conflicting appointments,
missing backup outcome, retrieved credential instructions, family isolation,
private/public joins, stale public data, two-source and evidence-limited
sysadmin escalation, private-cloud blocking, overnight job outcomes and
duplicate-file review. Its SHA-256 is
`b25b9deba2b5268c20b898e9745b0392ede32909d1e1ae33bad9b7527f55b4e6`.

The live repeat passed accepted production hash, health, `xe`, BMG G21 Vulkan,
memory, idle-worker and kernel-fault preflight, but stopped before candidate
startup because the prior trial's transient Qwen3.5-9B model had been correctly
removed. No inference case ran. The exit path restored and verified accepted
production, stopped candidate state and both active News timers.

Review found the first v3 runner armed restoration before artifact checks, so
this harmless preflight failure caused an unnecessary accepted-service restart.
The candidate now completes all immutable artifact checks before arming the
restoration trap or stopping any service. Re-acquiring the pinned model remains
a separately authorized download gate; the missing artifact must not be treated
as implicit permission to download it.
