# D4 tool-free development attempt 5 — 2026-10-24

## Execution result

The explicitly approved candidate-B run at digest
`7cb33aec4ac580774e884923b223ddd2427cd68fbc6e2b1da3899479d6630fb6`
completed the twelve-case schedule on the accepted Qwen3.5-9B Q4_K_M /
llama.cpp b11429 / SYCL service, but failed the structural admission boundary.

- Twelve model calls completed in 65.431 seconds; no retry ran.
- One answer was accepted as terminal `clarify`.
- Eleven answers were parsed JSON objects but were rejected as
  `nonterminal_contract` before their model-controlled text was retained.
- All eleven rejected answers selected a simulated `check` while also filling
  the terminal-only discrimination or verification fields.
- No simulated check ran after a rejected first response. There was no tool
  call, effect, service restart, lease or production change.

The mandatory prerequisite for blind review was twelve accepted terminal
sessions. It was not met, so candidate-B received no semantic review and the
frozen decision rule was not applied.

The owner-only journal remains at
`/root/aster-d4-development-evidence-20261024/attempt-5-ledger.jsonl` in LXC104,
mode 0600, SHA-256
`5681347664bccf7667f71a77a4f1d68a6096f147c359dd731400262d45999500`.
It contains 24 hash-chained rows and is 17,438 bytes. Temporary executable
sources were removed. Aster Agent, the accepted model service and Speech
remained active; the model service retained zero restarts and the lease
returned `ready`.

## Bounded correction

The failure was a response-contract mismatch rather than a diagnosis result.
The schema must expose the terminal fields on every branch because the local
JSON grammar has no conditional branch enforcement. The model populated those
fields while asking for a check, and the engine rejected the otherwise bounded
request.

The offline correction accepts correctly typed advisory values on a
nonterminal response, clears them before retention, and records only the
content-free Boolean `nonterminal_contract_cleared`. It continues to require
nonempty discrimination and an explicit unperformed verification for every
terminal response. It does not relax citation, effect, tool, check-budget or
completion-claim controls.

Candidate-B is spent and must not be replayed.
