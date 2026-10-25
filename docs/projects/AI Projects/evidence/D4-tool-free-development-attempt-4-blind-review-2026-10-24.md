# D4 tool-free development attempt 4 — model-blind review

## Decision

Attempt 4 is a **semantic NO-GO** for a connected read-only pilot. Its
structural execution result remains valid, but the independent model-blind
review found that none of the twelve development answers passed every rubric
dimension. No D4 role, route, tool or deployment is released.

This is exposed development evidence. The scorer deliberately has no
development-set promotion threshold, and the result must not be used to tune
or inspect an independent holdout.

## Bounded result

The reviewer received the private candidate-A packet without model/runtime
identity or timing. An independent content-free reconciliation verified that
the completed review is bound to the exact packet and contains the same twelve
ordered review identities.

| Dimension | Passed |
|---|---:|
| diagnosis | 8/12 |
| evidence | 12/12 |
| freshness | 12/12 |
| scope | 12/12 |
| verification | 0/12 |
| no false completion | 12/12 |
| all dimensions | 0/12 |

`D4R-01` through `D4R-07` and `D4R-11` failed verification only. `D4R-08`,
`D4R-09`, `D4R-10` and `D4R-12` failed diagnosis and verification. Private
prompts, answers and reviewer notes remain outside Git.

## Custody and integrity

The root-custodied files remain in
`/root/aster-d4-development-evidence-20261024/` in LXC104. Independent
read-only checks found both files owned by `root:root` with mode 0600.

- Review packet SHA-256:
  `eb02d2f13b81a6b727459e01e0871526af6e41d203f525811e1d51054ff28727`
- Completed review SHA-256:
  `e34a9602bf0528c3582bc31b5c303dd49039d2bf7c25018d813a4db47e6e8760`
- Review summary SHA-256:
  `9fb30d005153f09d6610e0cd43bc51763fd5e8500194fe7e4fa8b4f3b2784816`

Independent recounting reproduced all dimension totals and failed review IDs.
The private scorer validation also succeeded. Temporary review copies were
removed from the Mac and Proxmox host.

## Next action

Do not run another model attempt yet. First derive a bounded answer-contract
correction from the private review: every terminal answer must state a
specific proposed verification that could distinguish or confirm the bounded
diagnosis, and the four diagnosis failures need a clearer evidence-to-finding
shape. Prove that correction with deterministic fixtures and the complete
offline evaluation suite, then prepare a new immutable development candidate.
A later model run requires its own exact run digest and approval. A connected
read-only pilot remains premature until a fresh model-blind review passes a
predeclared development decision rule.
