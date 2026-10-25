# D4 tool-free development attempt 6 — 2026-10-24

## Fail-closed result

The explicitly approved candidate-C run at digest
`1e35bf540491cf00871584edb24d13486fa0de0ddf7d33d8320cc715ee694b92`
stopped during its first case after three model calls. The investigation engine
correctly cleared terminal-only advisory text from nonterminal check requests,
but the outer journal validator did not list the new content-free Boolean
`nonterminal_contract_cleared` among its allowed metadata fields. It rejected
the engine result before writing a finished row and required manual
reconciliation.

The partial owner-only journal is
`/root/aster-d4-development-evidence-20261024/attempt-6-ledger.jsonl`, mode
0600, SHA-256
`a123afce8d761f9104ca4b4c42447c28aafd292e1eef71c05b965d907e539943`.
It is 278 bytes and contains only the single hash-chained start marker. It is
uncertain by design and must never be resumed or replayed.

No second case began. No connected tool, effect, service restart, lease or
production change occurred. Aster Agent, the accepted model service and Speech
remained active; the model service retained zero restarts and the lease
returned `ready`. Temporary executable sources were removed. Candidate-C is
spent, no blind review ran, and no quality conclusion is possible.

## Closed integration gap

The validator now explicitly permits this one Boolean field and rejects every
non-Boolean value. A package-level test carries a canonicalized nonterminal
step through the validator and verifies the negative case. This closes the
integration path that the earlier component test did not exercise.
