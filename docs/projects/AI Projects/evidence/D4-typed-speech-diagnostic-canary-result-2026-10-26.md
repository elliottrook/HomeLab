# D4 typed Aster Speech diagnostic — one-run catalogue canary

**Date:** 2026-10-26  
**Result:** PASS  
**Restart:** none

## Execution

The installed report builder invoked the normal read-only HomeLab Doctor once
with schema 2 and schema 3 explicitly selected. Before publication it retained
the two existing LXC104 reports in a new root-only checkpoint and required the
new catalogue path and all `.new` staging paths to be absent.

The canary script had SHA-256
`c2894b005eddc2b6bbb3910aeb8d30c2e6664892acdef7dc280234b93369a108`.
Its private local result and transcript are retained at:

`~/lab/private-backups/aster-stream-a/typed-diagnostic-v3-canary-20261026-131717`

The root-only LXC104 predecessor checkpoint is retained at:

`/var/lib/aster/health/.typed-v3-pre-canary-20261026-131717`

## Bounded result

The schema-3 production file contains exactly two fixed states:

- `aster.agent_inference`: `pass`
- `aster.speech`: `pass`

The local and remote bytes matched for the aggregate, schema-2 sidecar and
schema-3 catalogue. Both typed files share the aggregate generation time and
exact SHA-256 binding. The production files are regular, one-link,
root:`aster` mode 0640 files with bounded sizes:

- aggregate: 4,248 bytes;
- schema-2 inference: 260 bytes;
- schema-3 catalogue: 303 bytes.

The catalogue exposes no Doctor summaries or probe output.

## Postchecks

- Aster Agent: active, `NRestarts=0`;
- accepted `aster-llama.service`: active, `NRestarts=0`;
- Aster Speech: active, `NRestarts=0`;
- scheduled report LaunchAgent: still idle, run count unchanged at 20;
- all three remote `.new` paths: absent.

The scheduled report's existing last-exit value remains 1 and was not changed
or retried by this canary.

## Boundary and next step

This result proves only fresh typed publication for two named read-only states.
It created no reader, caller, grant, model route, repair ability, automatic
routing or B60 effect.

The next task is an offline fixed `aster.speech` reader and deterministic
response. It must select only that check from a strict schema-3 catalogue,
bind it to the aggregate bytes, fail closed on any custody/freshness/shape
problem and keep authority `not-granted`.
