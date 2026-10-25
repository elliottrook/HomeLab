# F2 October 25 exact-cycle result — NO-GO

**Observed:** 2026-10-25 at 01:42 America/Vancouver. **Gate:** F2.
**Decision:** NO-GO; no retry in this cycle.

## Terminal evidence

The root-owned mode-0600 cycle state is schema
`aster-f2-scheduled.v1`, cycle `2026-10-25`, state `no_go`, with
`first_failure_phase=final` and
`failure_class=FINAL_GUARD_INSTALLED_PIN`. It contains zero archive-result rows.

The exact-date preparation timer fired at 01:15 PDT. Its service completed
successfully at 01:15:05. The final timer fired at 01:20; its service exited 1
at 01:20:01. The retained class proves that the final guard rejected the
installed-pin check before the archive scanner produced a result. No archive
integrity claim follows and this cycle must not be retried.

Post-observation checks found no F2, observer or `zstd` process, no whole-host
or application-B60 lease state/lock, and no trusted archive/source receipt.
`local-ai-lease status` was `ready`.

## Cleanup and production postcheck

Under the approved activation rollback, both October 25 exact-date timers were
stopped, disabled and removed, followed by a systemd daemon reload. They now
report not-found/inactive. Recurring F2 timers remain disabled/inactive.

LXC104, LXC110 and LXC116 remained running. Aster Agent, Aster Speech and the
accepted `aster-llama.service` were active; the llama unit hash remained
`a4c75169673a1a230682b73d362a05c1bdd30f7a5c41cfb9c77463204dfd4cb3`.
LXC114 was running, both News timers remained active/enabled, and Proxmox
`pvescheduler` and `pvestatd` were active. No production recovery was required.

## Consequence and next action

F2 remains open, so F3, the retained-receipt sequence and the full-stop drill
cannot advance. The platform owner must compare every installed file named by
the final guard with the exact expected pin set, identify the mismatched path
and preserve that bounded finding. Any correction needs offline and target-
Linux proof, a fresh exact-cycle card, independent review and explicit
activation approval. This result authorizes no retry, receipt, lease, service
stop, drill, A1 run or model call.
