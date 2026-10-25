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

## Fixed installed paths and pins

The effect transaction must use these exact installed files and no alternate
copy:

| File | SHA-256 |
|---|---|
| `evaluation_lease.py` | `5c5aa6c7174d53edb775f9a2640a867634b04a9b098d0742a589a1c2dc692686` |
| `evaluation_lease_adapter.py` | `6876e6892cae0d81c584fee7d6f3c5b79874d9b4737d250987f451f28b6aa910` |
| `evaluation_lease_entrypoint.py` | `0dab61905c834c36e3a865f8049c2650712422ddc27c534f1cd402b4e5ad52bb` |
| `stream_a_evaluation_watchdog.py` | `c406dd4da579d4d5129b13131121b55ac1aacaa1a5125c9d481e0d7f847c9849` |
| `stream_a_evaluation_owner.py` | `74c8072793cbbcc68e40d0548065f55031c2b8e5bfeab3d9583069aa4c8a22a1` |
| `stream_a_evaluation_owner_heartbeat.py` | `4c45a07098eb8cca31bf95bb50b0824b65c6772e636627b23219761f359ed6cc` |
| `stream_a_evaluation_restore_observer.py` | `70748eb15c50ff7008cadd85fe9affaf62c9ad3eb388ef962270f9f9389fc1d3` |
| `stream_a_evaluation_prepare_only_exercise.py` | `cf51b1d6546e27aebdef9e44ad4751343e38aa388c8eae682f9a476641f390fb` |
The fixed binaries/callbacks are:

- `/usr/local/sbin/stream-a-evaluation-lease`
- `/usr/local/sbin/stream-a-evaluation-owner`
- `/usr/local/sbin/stream-a-evaluation-owner-heartbeat`
- `/usr/local/sbin/stream-a-evaluation-watchdog`
- `/usr/local/sbin/stream-a-evaluation-restore-observe`
- `stream_a_evaluation_watchdog.py::run_watchdog_once` with
  `_restore_callback` only

Fixed custody paths are `/var/lib/local-ai-lab/stream-a-evaluation/lease.json`,
`lease.lock`, `lease.operation.lock`, `owner-intent.json`,
`owner-heartbeat.json`, `watchdog-status.json`, `restore-intent.json`, and
`/etc/local-ai-lab/stream-a-evaluation/watchdog-identity.json`.
The four consumer units are exactly `lxc104:aster-agent.service`,
`lxc116:aster-speech.service`, `lxc114:news-aggregator-ingest.timer`, and
`lxc114:news-aggregator-digest.timer`.

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
2. **Acquire:** write the root-owned `0600`
   `/var/lib/local-ai-lab/stream-a-evaluation/production-intent.json`, then
   invoke `/usr/local/sbin/stream-a-evaluation-lease --phase acquire --state
   /var/lib/local-ai-lab/stream-a-evaluation/lease.json --intent
   /var/lib/local-ai-lab/stream-a-evaluation/production-intent.json
   --effect-authorized`; require exact production admission and durable
   `prepared` state/lock.
3. **Quiesce:** invoke the same fixed entrypoint with
   `--phase quiesce --state /var/lib/local-ai-lab/stream-a-evaluation/lease.json
   --intent /var/lib/local-ai-lab/stream-a-evaluation/quiesce-intent.json
   --effect-authorized`; the exact intent contains only the generated lease ID,
   generation `1`, current epoch and heartbeat timeout `5`. It may mask/stop
   only the four baseline consumers; any uncertain command retains `quiescing`
   for recovery.
4. **Post:** invoke `/usr/local/sbin/stream-a-evaluation-lease --phase
   post-quiescence --state /var/lib/local-ai-lab/stream-a-evaluation/lease.json
   --intent /var/lib/local-ai-lab/stream-a-evaluation/post-intent.json
   --effect-authorized` with the exact admission and
   independent four-consumer/backend/auth/idle/GPU observations. Require
   `running` before any workload.
5. **D4:** invoke `/usr/local/sbin/stream-a-evaluation-lease --phase start
   --state /var/lib/local-ai-lab/stream-a-evaluation/lease.json --intent
   /var/lib/local-ai-lab/stream-a-evaluation/d4-start-intent.json
   --effect-authorized`, then the same fixed entrypoint with `--phase outcome`
   and `/var/lib/local-ai-lab/stream-a-evaluation/d4-outcome-intent.json`.
   Both intents contain the exact lease/generation and workload
   `d4-candidate-g`; outcome packet digest is the fixed D4 run digest and the
   timeout is 2160 seconds. Seal
   `/var/lib/local-ai-lab/stream-a-evaluation/d4-candidate-g.journal.jsonl`
   and `d4-candidate-g.result.json` as root-owned `0600` before M3.
6. **M3:** only after validated D4 outcome, revalidate the 11 exact LXC110
   inputs and manifest digest, then invoke the same fixed entrypoint with
   `--phase start --state /var/lib/local-ai-lab/stream-a-evaluation/lease.json
   --intent /var/lib/local-ai-lab/stream-a-evaluation/m3-start-intent.json
   --effect-authorized`, followed by `--phase outcome` with
   `/var/lib/local-ai-lab/stream-a-evaluation/m3-outcome-intent.json`.
   Seal `/var/lib/local-ai-lab/stream-a-evaluation/m3-nlu-calibration.journal.jsonl`
   and `m3-nlu-calibration.result.json` as root-owned `0600`.
7. **Restore/recover:** on normal completion, owner loss, deadline or command
   uncertainty, invoke recovery with the exact lease/generation and observed
   baseline. Require all four consumers restored and independent postcheck
   before clearing lease, lease lock, operation lock, identity, intent,
   heartbeat, status, restore intent and output/journal state.
8. **Cleanup:** use rollback checkpoint
   `/root/stream-a-evaluation-effectful-f6-rollback-20261025` and write a
   content-free result only after exact custody/absence,
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
