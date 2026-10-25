# D4 development attempt 10 preregistration — 2026-10-24

## Candidate-G representation correction

Candidate-F passed structural admission but failed its blind semantic gate.
Candidate-G changes the response contract and engine admission rules rather
than trying another prompt-only variation.

- `verification` is replaced by `post_change_verification`, making the field's
  role explicit and separate from the next diagnostic check.
- A terminal answer must cite at least one retained observation.
- A terminal answer must cite the result observation from every selected
  retained check; missing lineage fails closed as
  `selected_check_evidence_missing`.
- The instruction tells the model to select an unused retained check while one
  can resolve the uncertainty and budget remains.
- A clarification must state why the remaining retained checks cannot resolve
  the issue and name the alternatives.
- Post-change verification must describe the future bounded success condition
  and preserved state; it cannot substitute the diagnostic check or a proxy.

The fixtures, accepted Qwen3.5-9B Q4_K_M / llama.cpp b11429 / SYCL runtime,
12 sessions, 36-call maximum, tool-free boundary and 12/12 all-dimension gate
remain unchanged.

## Frozen identities

- Exact run digest:
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.
- Exact eleven-file source manifest SHA-256:
  `defaf6039e01c7ac0cc16b3c2a28568336335bc949ea8992ec288819d33c23b8`.
- Frozen candidate-G decision rule SHA-256:
  `35bedd86f244dc527606b463dcb223dde68c242c67d8028674d01553c5a9f089`.
- Complete offline suite: 165/165 passed.

Candidate-G has not run and its authority is `not-granted`. A later approval
must bind the exact run digest, a new owner-only attempt-10 journal, no retry
and the existing maximum. A fresh-history blind review remains conditional on
12/12 structural admission. Passing that semantic gate would make a separately
gated connected read-only pilot eligible for design; it would not deploy the
pilot or grant a tool.
