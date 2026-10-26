# Stream A evaluation fixed handlers — source candidate

Status: **SOURCE ONLY; RE-REVIEW REQUIRED AFTER TIMING BINDING**

This candidate supplies the fixed arm, workload-launch, recovery and cleanup
handlers used by the source-only sequence and effect-driver layers. It has no
CLI, is not installed, and cannot be invoked by a systemd unit or operator.

| Source | SHA-256 |
|---|---|
| `scripts/local-ai/stream_a_evaluation_handlers.py` | `6977af891af538989de49c6cc67f13fe7d6953b68a9bd9d44bc9edadbbeed4a4` |
| `scripts/local-ai/test_stream_a_evaluation_handlers.py` | `acba16d25e24b5e67b84c1dfa0be0d366f186b3c8784ca4f4389dc6b65321e60` |

## Fixed behavior

- Arming requires all five F6 units disabled/inactive, creates the fixed
  root-only checkpoint and owner intent without overwrite, enables the owner
  heartbeat timer before the watchdog timer, and continues only after an
  exact live owner identity, matching unexpired heartbeat and both active
  timers are observed.
- Workload launch accepts only candidate H followed by the fixed M3 command;
  each command's wall time is measured and bounded by the handler, then passed
  to a caller-supplied outcome verifier that must return the matching typed
  outcome with that exact elapsed value.
- Recovery bounds watchdog output to 16 KiB before parsing, stops the owner and
  either disarms a failed pre-lease arm or invokes
  the fixed watchdog until an exact bounded restored result is observed.
  Malformed or uncertain recovery retains state.
- Cleanup requires an independent restoration verifier, retains hashes of
  root-owned runtime evidence no larger than 64 KiB in the checkpoint, disables the watchdog and
  heartbeat timers, stops the owner, rechecks restoration, removes only the
  fixed runtime identity files and rejects residual lease/lock state.

The focused Stream A evaluation suite passes 72/72. Tests cover exact timer
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

## Independent review

The first review returned NO-GO because watchdog JSON and retained runtime
files were not size-bounded before parsing or hashing. Commit `f71adc1d`
added the 16 KiB and 64 KiB limits plus negative tests. Re-review returned GO
for this source-only handler layer. The deliberate remaining composition
boundaries above remain open and no installation or F6 arm is admitted. A
later source-only timing binding changed the reviewed hashes and therefore
requires a fresh review before this candidate can be accepted again.
