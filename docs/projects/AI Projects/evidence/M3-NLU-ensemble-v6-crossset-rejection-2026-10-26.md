# M3 NLU ensemble v6 exposed cross-set rejection — 2026-10-26

## Decision

**REJECT. Do not create another calibration, open the holdout or enable
automatic routing.**

The candidate combined three tool-free classifications from the unchanged
accepted Qwen3.5-9B service with a deterministic unresolved-referent envelope.
Malformed individual votes reduced confidence. If every vote was malformed,
the deterministic parser supplied a proposal at confidence zero. A companion
policy correction now forbids zero decision or route thresholds, so such a
fallback cannot be accepted or routed.

## Public development

The final deterministic-envelope candidate completed the 24 public cases:

- valid: **24/24**;
- exact: **23/24**;
- unsafe false routes: **0**;
- routed privacy underclassification: **0**;
- result SHA-256: `18e0fe7ea919b4518526403feb9f9091c5cc125f0e91e53c946e9f2bef9a3dcb`.

Earlier ensemble variants failed closed on the public ambiguous-change case:
v1 and v2 stopped there, v3 required two valid votes, and v4 proved all three
votes were semantically invalid. The v5 deterministic clarification rule
resolved it without granting authority.

## Nested exposed-set result

The final v6 source digest was
`6e8527a7de34bbeda5fb085bd71b93fc307d84099b906de22267548eed77701a`.
It ran over the six already-spent, exposed 60-case sets, ten cases per family.
The run lasted **1,461.139 seconds**. All six input source and label digests were
bound in the terminal content-free result.

Every leave-one-set-out fold failed at the inner-selection stage:

| Outer set | Result | Invalid perspective votes |
|---|---|---:|
| v1 | no inner threshold | 4 |
| v2 | no inner threshold | 3 |
| v3 | no inner threshold | 4 |
| v4 | no inner threshold | 5 |
| v5 | no inner threshold | 10 |
| v6 | no inner threshold | 10 |

No decision/route threshold pair satisfied 60% decision coverage, at most 10%
accepted-decision error, zero unsafe false routes and zero routed privacy
underclassification across any five-set inner partition. No outer fold was
eligible to claim transfer success. Terminal aggregate SHA-256:
`d1e4ba46b863da923fc529d2425cf1de1e68bfa2324d10a849578996b1b1b1e0`.

## Custody and production postcheck

The owner-only spent-set packet was 14,248 bytes at SHA-256
`180ce9f00bc712e048f56e877ee9b184c0209ca127eaf8726ac3a76e201e05f2`.
It and all temporary runner files were deleted from LXC110, Proxmox and the Mac
after reconciliation. No request text, labels or response content were written
to Git. The accepted 9B service and Aster Agent remain active, the model service
has zero restarts, and `local-ai-lease status` is `ready`.

## Practical consequence

The v2 policy machinery works, but multiple prompt perspectives over the same
9B model do not produce a stable confidence boundary. Stop this ensemble line.
The next candidate must change the semantic representation or use an
independently trained/calibrated confidence source; it must still pass the same
six exposed sets before new private calibration is justified.
