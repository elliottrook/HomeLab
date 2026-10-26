# Stream A evaluation fixed handlers — source candidate

Status: **SOURCE ONLY; INDEPENDENT REVIEW REQUIRED**

This candidate supplies the fixed arm, workload-launch, recovery and cleanup
handlers used by the source-only sequence and effect-driver layers. It has no
CLI, is not installed, and cannot be invoked by a systemd unit or operator.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_handlers.py` | `f8255bbe044cb970171ae972f6b55b9c1a85b74c51ef2cf7988b6e5c8ba7fae2` |
| `scripts/local-ai/test_stream_a_evaluation_handlers.py` | `e38e6e528dfdd79a7d0590d3661b9acc3286c323d681d6d5b01d477fb52f999e` |

## Fixed behavior

- Arming requires all five F6 units disabled/inactive, creates the fixed
  root-only checkpoint and owner intent without overwrite, enables the owner
  heartbeat timer before the watchdog timer, and continues only after an
  exact live owner identity, matching unexpired heartbeat and both active
  timers are observed.
- Workload launch accepts only candidate H followed by the fixed M3 command;
  each command is followed by a caller-supplied outcome verifier that must
  return the matching typed outcome.
- Recovery bounds watchdog output to 16 KiB before parsing, stops the owner and
  either disarms a failed pre-lease arm or invokes
  the fixed watchdog until an exact bounded restored result is observed.
  Malformed or uncertain recovery retains state.
- Cleanup requires an independent restoration verifier, retains hashes of
  root-owned runtime evidence no larger than 64 KiB in the checkpoint, disables the watchdog and
  heartbeat timers, stops the owner, rechecks restoration, removes only the
  fixed runtime identity files and rejects residual lease/lock state.

The focused Stream A evaluation suite passes 67/67. Tests cover exact timer
order, fixed workload commands, foreign-plan rejection, pre-lease disarm,
malformed and oversized recovery-result rejection, oversized retained-file
rejection, recovery retention and cleanup-after-restoration only.

## Remaining composition boundary

This source deliberately does not define the candidate-H or M3 output schema,
the independent restored-production observation, the accepted-cycle evidence
loader or a CLI. Those must be implemented and reviewed as fixed verifiers and
a single composition root before any installation or live approval. No F6
unit is enabled, no lease or identity is created, no consumer is stopped and
no model call follows from this source candidate.
