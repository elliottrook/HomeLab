# SA3 current proposal connected check — 2026-10-26

## Result

The current sanitized SA3 proposal boundary and fixed local transport passed a
three-stage synthetic connected check against the accepted local model. The
run completed in approximately 11 seconds and remained fully no-effect.

| Synthetic state | Accepted disposition | Selected check | Authority/effect |
|---|---|---|---|
| No observations | `observe` | `aster-gateway/status` | `none` / `none` |
| Gateway status observed | `observe` | `inference-server/status` | `none` / `none` |
| Gateway and inference status observed | `complete` | none | `none` / `none` |

This demonstrates that the accepted local model can follow the new progressive
contract: choose the first registered check, adapt to one sanitized observation,
and stop after the preregistered plan is exhausted. It does not grade diagnostic
quality on real incidents and does not release automatic routing, a producer,
repair authority or a broader sysadmin role.

## Preconditions and execution

- Local time at preflight was 23:51 PDT, more than one hour before the 01:15
  F2 window.
- `local-ai-lease status` was exactly `ready` before and after the run.
- LXC104 and LXC110 were running.
- `aster-agent.service` was active with PID `17250`, restart count zero.
- `aster-llama.service` was active with PID `48161`, restart count zero.
- No competing backup, archive scanner or lab lease was found.
- The exact source bundle SHA-256 was
  `14210a6fcf9ee008eaf326a303cc587dcbadebfbde31b3adf57ba24a9f1bae5f`.
- The runner independently required authenticated health and zero
  `requests_processing` before the first request and after the final response.
- Three serial synthetic calls used the fixed 45-second/512-token/16-KiB
  transport limits, thinking disabled, no tools and no retry.

Only bounded decision metadata was emitted. The credential, private reasoning,
hypothesis text and opaque evidence references were not retained.

## Postcheck and cleanup

The model and Aster Agent PIDs and restart counts were unchanged. The model was
idle and healthy, the lease remained ready, and temporary files were removed
from LXC110, Proxmox and the Mac.

## Local validation

- Connected-check unit tests: **2/2 passed**.
- Full `test_sysadmin*.py` suite: **60/60 passed**.
- `git diff --check`: passed.

## Source pins

| File | SHA-256 |
|---|---|
| `services/aster-agent/evals/sa3_current_proposal_check.py` | `611f9ce6c22237b7c9a75c54ed05da6a28a3a06b57c8031ed8923e629b5dfa1f` |
| `services/aster-agent/evals/test_sa3_current_proposal_check.py` | `704f8d8f87650403449f108cf3cd3cb2117b5adc187363827f06dea388504276` |

## Next gate

Build a representative, preregistered no-effect incident packet with explicit
quality scoring and independent review. The connected three-stage check proves
contract adherence only; it is not sufficient evidence for broad D4 acceptance.
