# D4 Candidate-J R3 postcheck policy reconciliation — 2026-11-05

## Corrected decision

Candidate-J R3 remains a spent transaction and is not retried. Its retained
public result is accepted as meeting the frozen public gate and may advance
only to a distinct untouched evaluation freeze. This correction does not make
a quality decision, expose an evaluation, enable routing, grant authority or
promote Candidate-J.

The earlier exact-cycle report remains retained, but its EPUB postcheck
interpretation is superseded. It compared the live system with the older
host-scheduled EPUB architecture. Before R3, the installed Lab Hours policy had
already changed to the registered-workload baseline: the legacy host scheduler
must be disabled/inactive, the guest monitor must be enabled/active, and the
guest worker must be inactive with a successful last result between booked
workloads.

## Exact R3 evidence

- Booking `aster-stream-a-sa3-candidate-j-20261105-0415-r3` claimed at
  04:15:00 PST and completed at 04:18:44 after 224 seconds.
- The authoritative ledger is `complete` / `COMPLETE`; the root terminal binds
  six requests, the exact registered workload and `production_restored=true`.
- The retained result is root-owned mode 0600, one regular link and 3,838
  bytes. Its file and canonical SHA-256 are both
  `ae5b10d72006bb3ffe7684440b7362828e9419bc6892ef97024c51b8b7c279c6`.
- The frozen scorer accepts 6/6 cases, exactly two model requests, four
  deterministic abstentions, zero retries, zero errors and zero effects.
- The frozen terminal reconciler returns `public_gate_met=true` and
  `quality_decision=eligible-for-distinct-untouched-evaluation-freeze`.

## Production-policy proof

The installed `full_inference_lab_sources.py` had the registered-workload EPUB
predicate before R3 and is pinned by the installed release manifest. The
authoritative Doctor emitted `state=healthy` with no codes at 04:11:46,
04:16:36 and 04:22:11 PST—before claim, while R3 was running, and after its
completion. The last of those records also observed R3 as the latest successful
restored transaction.

At 07:09 a recovery check initially followed the superseded EPUB branch and
temporarily enabled the old scheduler after a clear 2h15 ledger query and exact
file-pin check. The current Doctor immediately rejected that state with
`PRODUCTION_SERVICE_DOWN:EPUB_SCHEDULER`. The timer was disabled again and only
the newly admitted EPUB worker was stopped. The registered-workload baseline
was then revalidated: scheduler disabled/inactive, worker inactive/success,
lease ready, shared state and locks absent, and Doctor healthy with no codes.
No model, backend, route or core production service changed.

## Next gate

Freeze a distinct untouched Candidate-J evaluation and its model-identity-blind
review/decision contract without running it. The evaluation must remain
unexposed to implementation and selection work. Any later execution requires
its own registered workload, authoritative reservation and fresh runtime
gates. No public-development retry is justified.
