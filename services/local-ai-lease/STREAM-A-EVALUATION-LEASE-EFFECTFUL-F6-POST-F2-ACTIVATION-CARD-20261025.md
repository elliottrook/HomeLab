# Stream A effectful F6 activation — post-F2 candidate card

Status: **STATIC READY / LIVE BLOCKED; NOT AUTHORIZED OR RUN**

The prepare-only exercise passed and the workload artifacts are static-ready,
but this card is not activation approval. It defines the exact evidence and
separate gates required after the next backup/F2 window before any consumer
quiescence or model workload.

## Static evidence already verified

- Evidence commit: `e6c045a2`.
- D4 candidate-G archive remains local-user-owned mode `0600`, exactly 11 members,
  SHA-256 `d5a36cd02be6fdd3d0935e6ca1b23c1d0cad1329d72b04bb4048505fec7e3d47`.
- LXC110 M3 remains 11 root-owned mode-`0600` inputs, 98,414 bytes total,
  with exact hashes; `run.json`, `attempt-journal.jsonl` and `__pycache__` are
  absent.
- D4 run digest is
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`;
  M3 stage manifest digest is
  `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`.
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

## Frozen effect transaction — future approval only

Use one generated lease ID, generation `1`, and one same-cycle wall-clock
window `W`. The lease hard deadline is `W+4500` seconds, the restore deadline
is `W+5400` seconds, and the final 900 seconds are an unborrowable restoration
reserve. Bind the exact F2/F3/F4/F5 digests, D4 digest, M3 manifest digest,
four-consumer baseline and output/journal custody to that lease before any
effect.

The separately approved transaction is exactly:

1. **Arm:** create only the root-owned owner identity/intent for the exact
   lease/generation and arm the pinned owner, heartbeat and watchdog controls.
   Verify readiness without a lease or consumer mutation.
2. **Acquire:** invoke the fixed entrypoint with `--phase acquire --state
   /var/lib/local-ai-lab/stream-a-evaluation/lease.json --intent <0600-root-intent>
   --effect-authorized`; require exact production admission and durable
   `prepared` state/lock.
3. **Quiesce:** invoke `--phase quiesce` with the exact lease/generation,
   current time and heartbeat timeout. It may mask/stop only the four baseline
   consumers; any uncertain command retains `quiescing` for recovery.
4. **Post:** invoke `--phase post-quiescence` with the exact admission and
   independent four-consumer/backend/auth/idle/GPU observations. Require
   `running` before any workload.
5. **D4:** invoke the one approved candidate-G start/outcome under the exact
   run digest, archive and timeout. Seal output/journal custody before M3.
6. **M3:** only after validated D4 outcome, revalidate the 11 exact LXC110
   inputs and manifest digest, then invoke the one approved M3 start/outcome.
7. **Restore/recover:** on normal completion, owner loss, deadline or command
   uncertainty, invoke recovery with the exact lease/generation and observed
   baseline. Require all four consumers restored and independent postcheck
   before clearing lease, lease lock, operation lock, identity, intent,
   heartbeat, status, restore intent and output/journal state.
8. **Cleanup:** write a content-free result only after exact custody/absence,
   F2/F3/F4/F5 digest, production health, GPU holder, consumer baseline and
   timer checks pass. Never retry automatically.

Rollback checkpoint, command journal and output/journal paths must be root-
owned and mode `0600` (the D4 candidate archive remains local-user-owned
`0600` as measured). Any missing digest or custody drift is NO-GO.

## Separate effect gates — future approvals only

- **F6 arm:** separately approve creation of the root-owned owner identity and
  intent and arming only the pinned owner/watchdog/heartbeat controls. No lease,
  consumer stop, model call or workload.
- **Quiesce/post gate:** separately approve the exact lease `quiesce`, then
  read-only post-quiescence validation. It may mask/stop only the four
  registered consumers and must retain the restoration reserve.
- **D4 candidate-G:** separately approve one workload start and outcome under
  its exact archive/hash/timeout contract and run digest
  `03b0ad74a862ee04de75e012f52f6662c61192b69b279ea4d1d66c80d9ff9153`.
  Candidate-G approval is unspent and cannot be inferred from static readiness.
- **M3:** separately approve only after D4 has a validated outcome and the
  exact LXC110 input set and manifest digest
  `69ffc58928ebd2f2f64e0600b8c4a7d73ce5f5356c485e1df8c2265741972165`
  remain unchanged. The full restore/reconciliation gate remains mandatory.

Any failure, stale evidence, owner loss, backend/GPU drift, uncertain command,
F2/F3/F4/F5 overlap or incomplete restoration retains evidence and stops. No
automatic retry, schedule modification, consumer bypass or model call is
permitted.
