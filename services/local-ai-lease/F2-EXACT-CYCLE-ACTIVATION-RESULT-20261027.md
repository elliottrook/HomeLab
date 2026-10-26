# F2 exact-cycle activation result — 2026-10-27

**Result:** PASS — scheduled conditionally.
**Activated:** 2026-10-26 07:25 PDT.
**Source:** `9550e53aad222f0a4d45ceb2ae1632a50e93fb3d`.
**Authorization:** Jason explicitly approved this exact activation.

## Installed one-shot units

| Unit | Trigger | Installed SHA-256 | State |
|---|---:|---|---|
| `f2-preflight-prepare-20261027.timer` | 2026-10-27 01:15 PDT | `7551c94a7b3d367059724aecb7b32863ad341fa9fb39a4ce08b04ea8d760493d` | enabled, active, waiting |
| `f2-preflight-final-20261027.timer` | 2026-10-27 01:20 PDT | `2cdb512508ac4d889c4c1b94fdb6d42d95504cb721b2e450e7ad572b56592cd6` | enabled, active, waiting |

Both units are `root:root 0644`, regular one-link files. Calendar resolution,
`systemd-analyze verify`, source hashes and unit hashes passed. Neither service
was manually started. The recurring F2 timers remain disabled and inactive.

## Static validation

- All five installed F2 dependency hashes matched the reviewed card, including
  corrected coordinator `6a1d520a…8193`.
- The installed default-launcher assertion passed.
- The focused installed coordinator suite passed 15/15.
- The broader clean target-Linux suite completed 51/51: 50 passed and one
  expected skip.
- The October 27 state, lease, locks and retained receipt were absent.
- The October 26 terminal-state digest remained
  `51e296ea56cdf37af4a991ee33d3eaac38efa7865fa5212c707b823ce7320de6`.
- LXC104/110/116, Aster Agent, accepted `aster-llama` SYCL service, Speech,
  News timers, `pvescheduler` and `pvestatd` were healthy after activation.
- The one-occurrence observation and cleanup heartbeat is active for 01:42 PDT
  as `aster-f2-october-27-reconciliation`.

## Boundary

**TIMED TEST: GO — SCHEDULED / CONDITIONAL.** The 00:30 Proxmox backup, 01:00
TrueNAS task 1, exact archive identities, host load, exclusion and quiet-host
conditions remain fresh fail-closed runtime gates. Any failed or uncertain gate
produces terminal NO-GO without retry. This activation authorizes no F3 receipt,
lease, consumer stop, model call or recurring schedule.
