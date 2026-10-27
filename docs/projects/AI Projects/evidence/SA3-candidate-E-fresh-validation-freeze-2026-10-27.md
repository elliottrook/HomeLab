# SA3 candidate-E fresh validation freeze — 2026-10-27

Candidate E is fixed at commit `73901010`. This second fresh packet is frozen
before execution and must not be used to alter candidate E.

The eight cases cover an empty incident, gateway-first failure, two
inference-first out-of-order observations, an instruction-like string inside
unavailable evidence, and four exhausted-plan combinations spanning all-fail,
unavailable-plus-warning, all-ok and warning-plus-failure. Expected results
require the remaining registered check in every partial state, deterministic
completion for fully available evidence, deterministic escalation for exhausted
unavailable evidence and citations for every exposed observation.

| File | SHA-256 |
|---|---|
| `services/aster-agent/evals/sa3-current-proposal-fresh-v2.json` | `ce3acf2f3009c019fa509404ab3e67945f4d24e810cc247d63e1cdf50c4890b3` |
| `services/aster-agent/evals/sa3_current_proposal_eval.py` | `805e494730663d841df219aeff75ce7fa80a87d0d7eb5a5b2b572dfc632d4ca4` |
| `services/aster-agent/evals/test_sa3_current_proposal_eval.py` | `543663ac1e88c965d7a38e0a3035e9489de5a83a6b2759212e09ec47d6409b9b` |

Packet-loader/scorer tests pass **7/7**. Run the eight cases once with the fixed
transport, no retry, no retained prose, only after idle/lease checks and with a
safe margin before F2. Any failure rejects candidate E.
