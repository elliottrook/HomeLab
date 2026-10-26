# D4 fixed Aster Speech — blind comparison result

**Date:** 2026-10-26  
**Decision:** **GO — narrow fixed-Speech usefulness gate passed**

## Execution

The accepted Qwen3.5-9B service reviewed the exact frozen eight-case packet as
an implementation-blind judge. The reviewer saw only each synthetic question,
responses A and B, and the fixed rubric. It did not receive the A/B mapping or
the acceptance threshold. The run used temperature zero, one request at a
time, a 60-second per-case timeout and a 600-second outer deadline.

Before the run, LXC110 was running, `aster-llama.service` was active with zero
restarts, the shared lease was ready and the exclusive output path was absent.
The service was not restarted or reconfigured.

## Bound result

| Measure | Result | Acceptance |
|---|---:|---:|
| fixed answer preferred | 8/8 | at least 6/8 |
| fixed answer passes all five dimensions | 8/8 | at least 7/8 |
| fixed-answer unsafe claims | 0 | exactly 0 |
| aggregate answer preferred | 0/8 | informational |
| ties / neither | 0 / 0 | informational |

- packet SHA-256:
  `8a8e0a9b2d45fe49daf7b4563a13edd65a93b75c3cf8dca0f58c146e92722f10`;
- review SHA-256:
  `02aa62c748577f666b39b43f946f021435df8843b5674416dc7e3c71dd523f37`;
- content-free result SHA-256:
  `c2059d3601c37e0d3ec07ac79e38877755b7a41201e5eac75eace59a6f632371`;
- reviewer identity: `aster-qwen3.5-9b-independent-blind-reviewer`;
- review runner SHA-256:
  `c7e28e6182ab82ccbc70d7ec379b84ecf162f335ca79b64d0939df6c1367e715`.

The focused fixed-Speech suite passes 14/14 after the run. Independent
postchecks found the accepted model service active with zero restarts.

## Decision boundary

This result closes the practical-usefulness gate for the narrow deterministic
Speech-status answer. It does not authorize automatic routing, grant repair or
administrative authority, broaden the observation schema, or support a claim
about general diagnostic quality. The route remains explicit, read-only and
`authority: not-granted`.
