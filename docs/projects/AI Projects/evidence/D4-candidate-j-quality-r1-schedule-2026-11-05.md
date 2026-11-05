# D4 Candidate-J quality R1 schedule — 2026-11-05

## Result

Candidate-J's distinct untouched-quality transaction is scheduled under the
authoritative Lab Hours ledger:

- booking `aster-stream-a-sa3-candidate-j-quality-20261105-1016-r1`;
- owner/workload `aster-stream-a` /
  `sa3-evidence-matrix-candidate-j-quality-v1`;
- window 10:16–11:16 PST (`-07:00`), start epoch `1793898960`, end epoch
  `1793902560`;
- state `scheduled`, with the required 900-second restoration reserve.

The first proposed 08:30 window conflicted with the existing TTS experiment.
That booking owns 08:30–10:00 and its recovery reserve protects the stack
through 10:15. The authoritative check returned the complete 10:16–11:16
window clear before the Candidate-J reservation was created. No existing work
was cancelled, shortened or overlapped.

## Static evidence

The installed release remains
`aster-tts-dual-cpu-screen-plus-candidate-j-quality-v1`; all 46 manifest pins
reread exactly. The Candidate-J quality workload is registered and admitted.
LXC104/110/116 are running; Aster Agent, accepted llama.cpp/SYCL, Speech,
`pvescheduler` and `pvestatd` are active. Dispatcher and Doctor timers are
enabled and active and both last service results are success/exit zero. No
restart or model/backend change occurred.

## Remaining fresh gates

The dispatcher owns the once-only claim. At 10:16 it must recheck the exact
reservation and installed pins, acquire the whole-host lease and shared
operation lock, verify the quiet-host and production baselines, and retain a
bounded terminal result. Success requires exactly 20 rows, 14 model requests,
six no-transport abstentions, zero retries/errors/effects, restored production,
no residual Candidate-J state/process/locks and healthy postchecks. Any failed,
late, changed or uncertain gate is a terminal NO-GO without retry.

Blind review and any promotion decision remain downstream of a complete
transaction. This schedule grants no route, tool authority, restart,
model/backend change or automatic promotion.
