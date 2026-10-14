# Application-only B60 controller candidate — 2026-10-14

## Result

The application-only B60 lease now has an offline controller candidate. It
persists a secret-free lease record before effects, stops and restores only
`aster-agent.service` in LXC 104 and `aster-speech.service` in LXC 116, and
has no command path for LXC 110 `aster-llama.service`. Invalid receipts and
advisory mode fail before any command is issued.

The controller is intentionally not installed or enabled on Proxmox. The
whole-host recovery drill remains a separate 03:15 path; this application
mode is the only path that can support a sidecar benchmark while llama.cpp
stays active.

## Evidence

- `scripts/local-ai/application_b60_controller.py`
- `scripts/local-ai/test_application_b60_controller.py`
- `services/local-ai-lease/APPLICATION-B60-BENCHMARK-RUN-CARD.md`
- Full local suite: **76 passed, 2 skipped**.
- Focused controller behavior: acquire/restore allowlist, explicit LXC110
  denial, advisory no-effect behavior and invalid-receipt fail-closed behavior.

## Remaining live gate

Before a benchmark can run, the platform still must produce a distinct
source-bound application receipt, install the exact sidecar and host-owned
observation probes, and perform the scheduled recovery/restore validation.
No model calls are authorized by this candidate alone.
