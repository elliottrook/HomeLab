# F2 October 24 exact-cycle activation result

**Activated:** 2026-10-23 after Jason's explicit approval. **Scope:** the two
reviewed October 24 one-shot timer units and one observation-only reconciliation
heartbeat.

## Preflight and installation

Immediately before activation, Stream A re-read the five installed F2 source
hashes and root:root 0644 custody, confirmed the reviewed candidate hashes,
and verified absence of the October 24 cycle state, cooperative lease state and
lock, and trusted F2 receipt. Recurring F2 timers remained disabled/inactive.

The two candidates from platform commit
`054ada0698d4b35cf99217b1d6fe7bac97ff1cb3` passed target-side systemd unit and
calendar validation, were installed root:root 0644, and were enabled without
manually starting either service.

| Timer | Installed SHA-256 | Next trigger |
|---|---|---|
| `f2-preflight-prepare-20261024.timer` | `0b13bcd78b6ec1623f35942bcbc9f7ae63a03433223058eac25ce0920df53376` | 2026-10-24 01:15 PDT |
| `f2-preflight-final-20261024.timer` | `81c7cb6a57c95f946d85348f856852db9839f469acd76ad21a3c15511a666860` | 2026-10-24 01:20 PDT |

Both units report enabled and active. The recurring timers remain disabled and
inactive. LXC104/110/116 are running and `pvescheduler`/`pvestatd` are active.

## Reconciliation control

The existing `aster-archive-integrity-timing-check` heartbeat was updated to
one active occurrence at 01:42 Vancouver on October 24. It is observation-only:
it cannot invoke, retry, extend or reschedule F2, acquire a lease, create a
receipt, stop production, call a model or advance F3. It must record the
terminal result, remove/disable only the spent exact-date units, keep recurring
timers disabled, and notify the platform owner.

## Remaining volatile gates

Activation does not establish that the future 00:30 Proxmox backup or 01:00
TrueNAS task 1 will complete. The prepare/final services must fail closed if
any fresh-cycle, load, source-pin or competing-work gate is absent. No scan
result is claimed until the 01:42 reconciliation reads terminal evidence.
