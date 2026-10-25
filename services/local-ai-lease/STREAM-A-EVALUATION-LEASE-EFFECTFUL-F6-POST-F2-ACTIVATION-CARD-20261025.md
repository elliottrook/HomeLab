# Stream A effectful F6 activation — post-F2 candidate card

Status: **STATIC READY / LIVE BLOCKED; NOT AUTHORIZED OR RUN**

The prepare-only exercise passed and the workload artifacts are static-ready,
but this card is not activation approval. It defines the exact evidence and
separate gates required after the next backup/F2 window before any consumer
quiescence or model workload.

## Static evidence already verified

- Evidence commit: `e6c045a2`.
- D4 candidate-G archive remains root-owned mode `0600`, exactly 11 members,
  SHA-256 `d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.
- LXC110 M3 remains 11 root-owned mode-`0600` inputs, 98,414 bytes total,
  with exact hashes; `run.json`, `attempt-journal.jsonl` and `__pycache__` are
  absent.
- Fresh Python `3.12.14` / Pydantic `2.13.4` NLU suite passed `126/126`.
- Candidate-G approval remains approved and unspent; no model call or consumer
  effect occurred.
- The exact prepare-only exercise passed with zero consumer commands and full
  cleanup; its receipt and digests are recorded in the exact-retry card.

## LIVE BLOCKED preconditions

No effectful phase may start until all are freshly reverified in the same
backup cycle:

1. Fresh F2/F3/F4/F5 evidence is complete, independently reread and bound to
   the proposed lease/generation. The post-backup settling window and the
   restoration reserve must fit without overlap.
2. Whole-host lease is ready; production backend/auth/idle/GPU observation is
   exact; all four consumers are at the exact enabled+active baseline; F6
   units/timers are disabled/inactive; F2 timer identities and next runs are
   unchanged.
3. Installed source/custody pins, owner identity path, operation lock and
   rollback checkpoint match the accepted inactive cards. Any drift is NO-GO.

## Separate effect gates — future approvals only

- **F6 arm:** separately approve creation of the root-owned owner identity and
  intent and arming only the pinned owner/watchdog/heartbeat controls. No lease,
  consumer stop, model call or workload.
- **Quiesce/post gate:** separately approve the exact lease `quiesce`, then
  read-only post-quiescence validation. It may mask/stop only the four
  registered consumers and must retain the restoration reserve.
- **D4 candidate-G:** separately approve one workload start and outcome under
  its exact archive/hash/timeout contract. Candidate-G approval is unspent and
  cannot be inferred from static readiness.
- **M3:** separately approve only after D4 has a validated outcome and the
  exact LXC110 input set remains unchanged. The full restore/reconciliation
  gate remains mandatory.

Any failure, stale evidence, owner loss, backend/GPU drift, uncertain command,
F2/F3/F4/F5 overlap or incomplete restoration retains evidence and stops. No
automatic retry, schedule modification, consumer bypass or model call is
permitted.
