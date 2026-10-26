# Stream A D4/M3 outcome verifier — source candidate

Status: **SOURCE ONLY; INDEPENDENT REVIEW REQUIRED**

This pure verifier converts the two fixed private workload artifacts into the
content-free hashes and bounded call counts needed by the evaluation lease.
It has no CLI, filesystem, subprocess, network, credential or model effects.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_outcome_verifier.py` | `7f897ed25514b47dabfdd46919b20f7ed47424258af220c43f8eecbf8a954c0f` |
| `scripts/local-ai/test_stream_a_evaluation_outcome_verifier.py` | `d9134cacc3d4374b4e89230ac3661e8111f7ceba5c24a753d957722b50c65059` |

The D4 verifier accepts only a 1–4 MiB hash-chained journal bound to the fixed
candidate-H run digest, the exact `sa3-dev-01` through `sa3-dev-12` identity
set, and exactly twelve alternating started/finished
non-thinking sessions, terminal conclude/clarify results, no failure and at
most 36 calls. It returns the full-journal digest and a canonical content-free
summary digest.

The M3 verifier accepts only an exact run object up to 4 MiB and an attempt
journal up to 1 MiB, bound to the frozen candidate, release, engine and policy
identities.
It requires sixty unique completed records, completely typed and
semantically valid no-authority interpretation or bounded failure rows, and
the exact 122-row journal sequence. It returns
the journal digest, a canonical content-free summary digest and 60 calls.

The combined Stream A evaluation suite passes 78/78, including broken D4
chains, arbitrary D4 case substitution, nonterminal D4 results, duplicate M3
cases, malformed interpretation dimensions, journal drift, duplicate JSON
keys and oversize artifacts.

## Remaining integration boundary

The source does not read guest files. A later reviewed guest-local wrapper must
open the exact files with no-follow, root/identity custody and fixed byte
bounds, then emit only the three content-free verifier fields. The Proxmox
composition root must authenticate that wrapper result and combine it with the
handler-measured elapsed time. No installation, workload or model call is
authorized by this source candidate.
