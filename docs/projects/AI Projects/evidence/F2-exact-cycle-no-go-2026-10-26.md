# F2 exact-cycle result — 2026-10-26

**Decision:** NO-GO. The approved October 26 read-only F2 attempt reached its
terminal observation state, but did not produce an archive timing result.

The root-custodied state for cycle `2026-10-26` reports:

- state: `no_go`
- first failure phase: `final`
- failure class: `OBSERVER_COMMUNICATION_FAILED`
- archive result rows: none

The date-specific preparation and final timers triggered at 01:15 and 01:20
PDT. Their systemd timer results were successful, which proves only that the
timers dispatched their services; it does not satisfy F2. The bounded terminal
state is authoritative. The failure class does not identify the underlying
observer communication defect, so this record does not infer a cause.

The observation-only cleanup removed and disabled both October 26 timer units.
The recurring F2 timers remain disabled and inactive. Postchecks found no F2
or `zstd` child, lease, lock or trusted receipt. LXC104, LXC110 and LXC116 were
running; Aster Agent, the accepted `aster-llama` SYCL service, Speech,
pvescheduler and pvestatd were active; the News timers remained active and
enabled.

F2 therefore remains failed and unmeasured for this cycle. F3 must skip and
write no receipt; F4–F9, the full-stop drill and A1 remain closed. This cycle
must not be retried.

The next safe action is for the platform owner to diagnose the bounded observer
communication path without replaying this cycle, preserve a more specific
failure code, prove any correction offline and on target Linux, and present a
fresh exact-cycle card for review and separate approval.
