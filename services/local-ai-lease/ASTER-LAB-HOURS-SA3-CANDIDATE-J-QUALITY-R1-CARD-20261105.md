# Aster Lab Hours SA3 Candidate-J quality R1 card — 2026-11-05

## Exact reservation

- Booking: `aster-stream-a-sa3-candidate-j-quality-20261105-1016-r1`
- Owner/workload: `aster-stream-a` /
  `sa3-evidence-matrix-candidate-j-quality-v1`
- Window: 2026-11-05 10:16–11:16 host-local offset `-07:00`
- Epochs: start `1793898960`, end `1793902560`
- Recovery reserve: 900 seconds

The authoritative ledger rejected the proposed 08:30–09:30 and 10:00–11:00
windows because booking `aster-tts-dual-cpu-20261105-0830` owns 08:30–10:00
plus its restoration reserve through 10:15. The complete 10:16–11:16 window
returned `clear` before this exact registered booking was saved as
`scheduled`. The TTS work is not cancelled, shortened or overlapped.

## Static GO evidence

Approved R2 bundle `5a1424b5…fd6e` is installed inactive. The combined release
is `aster-tts-dual-cpu-screen-plus-candidate-j-quality-v1`; all 46 release
pins reread exactly. The fixed workload is admitted and the booking names that
exact workload. LXC104/110/116 are running; Aster Agent, accepted
`aster-llama.service`, Speech, `pvescheduler` and `pvestatd` are active.
Dispatcher and Doctor timers are enabled and active and both last services
report success/exit zero. No restart or model/backend change was made.

## Runtime and terminal boundary

At claim the dispatcher must freshly recheck this exact reservation, installed
pins, ready lease, shared operation lock, quiet-host boundary, production
health, exact start and recovery allowance. Accept success only for 20 valid
rows, exactly 14 model requests, six deterministic no-transport abstentions,
zero retries/errors/effects, a bounded canonical result, exit zero,
`production_restored=true`, no remaining Candidate-J process/state/locks and
healthy production postchecks.

Any changed, missing, late, conflicting or uncertain gate is terminal NO-GO
without retry. Retain only bounded root-custodied evidence. This booking
authorizes only Candidate-J quality R1. It does not authorize a retry,
model/backend change, restart, route, tool grant, repair authority or automatic
promotion.
