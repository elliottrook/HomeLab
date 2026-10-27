# M3 NLU decomposed microtasks public rejection — 2026-10-26

## Decision

**REJECT before private evaluation.** Six narrow independent model calls for
action, domain, privacy, referent completeness, safety override and source
composition produced 24/24 structurally valid public results, but only 7/24
complete interpretations were exact. No unsafe false route or routed privacy
underclassification occurred. Automatic routing remains off.

## Mechanism and boundary

This was a task-mechanism change after closing prompt-based whole-label
selection. Each call could return only one typed semantic value and could not
name a disposition, capability, provider, route, tool or authority. Existing
deterministic policy assembled the six values into the interpretation contract.
The public fixture was pinned at
`1565a21c78875f64f4f25a190e977ae34dc01bdfcfd5e49c056e8365268b3785`.

The complete dependency-free NLU suite passed 422/422. The first target attempt
found an incomplete temporary archive and stopped at import before any model
request. Adding the omitted import-only module repaired packaging without
changing candidate logic; the bounded run then completed in 84.018 seconds.

## Content-free result

| Dimension | Exact |
|---|---:|
| request family | 20/24 |
| sensitivity | 21/24 |
| capabilities | 11/24 |
| ambiguity | 13/24 |
| disposition | 13/24 |
| reason | 13/24 |
| all dimensions | 7/24 |

Run SHA-256 was
`e1bfddaa93a18aa03c38edb6975d0ca25d9b8bb4fede0530dd194b64c894c2d0`.
The decomposition improved family and sensitivity recognition, but independent
referent and domain/action judgments did not compose reliably enough for the
deterministic policy to recover capabilities and disposition.

## Postcheck and consequence

The accepted 9B/SYCL service remained active on the same PID with zero restarts
and the whole-host lease returned `ready`. No model, service, schedule, key,
grant, route or production file changed.

Do not tune these six microtask prompts against private sets. The next candidate
must supply a learned or otherwise coherent joint semantic representation; more
prompt decomposition is closed. The sealed holdout remains unopened.
