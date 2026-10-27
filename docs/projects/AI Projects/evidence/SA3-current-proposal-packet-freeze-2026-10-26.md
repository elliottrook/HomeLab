# SA3 current proposal packet freeze — 2026-10-26

## Purpose

Freeze a representative public synthetic packet before a connected run so the
expected answers cannot be changed after seeing model output. This evaluates
the current sanitized SA3 proposal contract, not the historical open-ended SA3
runner.

## Packet

Eight cases cover:

- no observations;
- gateway `ok`, `warn` and `unavailable` states with inference status still
  available as the remaining registered discriminator;
- both registered statuses `ok`;
- inference status `unavailable` after a healthy gateway;
- gateway warning plus inference failure; and
- both registered sources unavailable.

The preregistered expected outcomes require the model to choose the next fixed
check while evidence remains, complete when the bounded evidence supports a
conclusion, and escalate when exhausted evidence remains unavailable. Every
available evidence item must be cited. The trusted boundary must accept the
proposal and return literal no-authority/no-effect output.

## Scoring and retention

The exact scorer records only case ID, pass/fail, disposition, selected
target/kind, citation count or a bounded error class. It does not retain model
prose, reasoning, evidence references or credentials. One wrong disposition,
selection, citation count, validation failure or effect-boundary failure fails
that case. This packet grants no automatic promotion.

Offline tests pass **5/5**, including exact scripted acceptance, wrong-answer
failure, content-free malformed-response handling and duplicate-key rejection.

## Source pins

| File | SHA-256 |
|---|---|
| `services/aster-agent/evals/sa3-current-proposal-packet.json` | `7bd0d142d600391251632adf317fbd70c80f96b839d5a648acf9ea931ca39516` |
| `services/aster-agent/evals/sa3_current_proposal_eval.py` | `a18e45afd8330ebf792d76c4f62ff9f28b8fe4ff9b5d8034033480406cb9f05e` |
| `services/aster-agent/evals/test_sa3_current_proposal_eval.py` | `0d58b552068fd167cad48930094f3e72ec9b04e7f74c7932d0f06bc5f12dfefd` |

## Connected-run gate

Run the frozen eight cases once with the fixed local transport only when the
lease is ready, the accepted service is healthy and idle, no backup or F2 work
competes, and sufficient margin remains before the 01:15 F2 window. Use no
retry. Recheck unchanged service identity and idle health, remove temporary
files, and record the exact aggregate result.
