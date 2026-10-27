# M3 NLU constrained whole-label public gate — 2026-10-26

## Decision

**REJECT the prompt-based whole-label family before private evaluation.** The
best revision reached 20/24 exact with zero unsafe false routes and zero routed
privacy underclassification, below the fixed 23/24 public admission floor. A
final bounded rubric revision regressed to one unsafe false route. No private
cross-set, calibration set or holdout was opened, and automatic routing remains
off.

## Materially different formulation

Instead of asking the accepted local 9B model to synthesize six independent
interpretation fields, the candidate exposed 16 coherent complete labels from
the public development ontology. Each label had a stable digest-derived ID.
The model could return only `{"label_id":"..."}` under a strict JSON schema;
local code mapped that ID to the complete label and applied a tightening-only
deterministic safety review. The response could not name a provider, route,
tool, confidence, permission or authority.

The oracle path represented all 24 public cases exactly. The dependency-free
NLU suite passed 416/416 after the final revision. Catalogue SHA-256 was fixed
across all live runs at
`aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44`.

## Public-only live results

Fresh prechecks found the whole-host lease ready and the accepted 9B/SYCL
service active with `NRestarts=0`. Each revision ran twice against the same
24-case public fixture. Within each revision, all 24 decisions were identical
across repeats.

| Revision | Exact | Unsafe false routes | Routed privacy underclassification | Elapsed seconds | Decision |
|---|---:|---:|---:|---|---|
| v1, catalogue only | 16/24 | 4 | 1 | 15.131 / 13.730 | reject |
| v2, general semantic rubric | 20/24 | 0 | 0 | 15.386 / 13.894 | reject |
| v3, final ambiguity/future rubric | 21/24 | 1 | 0 | 15.468 / 13.849 | reject and close family |

The v2 policy SHA-256 was
`a1edf89e343000654e55b32dbd67a99ce7f0e4e297d181e85f911642fc916d92`.
Its stable failures were two family choices for incomplete referents and two
sensitivity choices for unsupported future/lottery requests. The v3 policy
SHA-256 was
`20fbe15589e52e73a8a8164cb3602420501de4e80ee8c22237110da531071ea3`.
It repaired the two incomplete-referent decisions, but one multi-source
personal research request lost its web/join composition and one impossible
future request became an unsafe factual route. Prompt repair therefore traded
one error class for another instead of clearing admission.

## Production and privacy postcheck

The accepted 9B service remained active on the same process with zero restarts,
and the whole-host lease returned `ready`. No model, service, schedule, key,
grant, production file or route changed. Results retained only case IDs,
complete content-free labels, timing and digests. The request text remained in
the already-public fixture; no private example or answer was retained.

## Consequence

Do not add another prompt rubric to this family and do not expose it to the six
spent private sets or the sealed holdout. Together with the earlier semantic
slot failures, this shows that constraining output shape improves safety but
does not supply a sufficiently reliable semantic representation. The next M3
candidate must change the representation or training/task mechanism and must
retain deterministic deny/abstain, privacy floors, capability allowlisting and
the no-authority boundary.
