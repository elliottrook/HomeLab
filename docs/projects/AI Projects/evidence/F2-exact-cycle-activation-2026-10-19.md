# F2 exact-cycle activation — 2026-10-19

Status: **ARMED FOR ONE CYCLE; RESULT NOT YET MEASURED**

Jason approved activating the reviewed October 20 F2 schedule. The platform
owner's exact-cycle source is commit `f5d76d84`; its two timers have fixed
Vancouver dates and no recurrence.

## Installed state

Stream A verified the existing coordinator and service pins before installing
only these root-owned mode-0644 timer units on Proxmox:

| Unit | SHA-256 | Elapse |
|---|---|---|
| `f2-preflight-prepare-20261020.timer` | `01c819c23b0b04e415884b44dd34454e28b8dee4aa76bd8dac8c186e4b775449` | 2026-10-20 01:09 PDT |
| `f2-preflight-final-20261020.timer` | `cd8ac10fd6b0df9b8641ed2bb8961873cf4e65eacbfca92b3145b344e7e55768` | 2026-10-20 01:10 PDT |

Both exact-date timers are enabled and active, with the expected next-elapse
times. The old daily timers remain disabled. The prepare and final services
are inactive, the scheduled-state directory is empty, and no scan, receipt,
lease, service stop or model call occurred during activation. The source
staging was removed. The absent-target rollback marker is retained at
`/root/aster-f2-exact-cycle-rollback-f5d76d84/targets-were-absent`.

## Independent observation

The Codex automation formerly responsible for attempting the scan at 01:05
has been replaced with a one-occurrence 01:42 post-run observer. It is expressly
barred from starting or retrying the scanner. It will validate the bounded
terminal state and postconditions, disable the spent exact-date timers, update
the evidence, and report a complete result or the exact NO-GO gate.

This activation closes the scheduling gap only. F2 remains open until the
October 20 cycle produces exactly three valid, exit-zero archive rows within
the approved bounds and a clean postcheck.
