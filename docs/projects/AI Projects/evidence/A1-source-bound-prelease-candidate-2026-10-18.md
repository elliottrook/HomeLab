# A1 source-bound pre-lease candidate — 2026-10-18

**Status:** offline, uninstalled candidate. No host observation, lease,
watchdog, model call, or production effect occurred.

`application_b60_prelease.py` defines a typed adapter boundary for the
platform-owned pre-lease producer. It collects one cycle from fixed source
classes for the Proxmox backup chain and application-bound receipt, TrueNAS
task 1 and fixed schedules, the 104/110/116 Mac-subset identity and mirror,
and LXC/runtime consumers, backend identity and News quiescence.

It binds all observations to one cycle and owner-controlled clock, requires
fixed source identifiers and verified flags, rejects future or partial
observations and arbitrary receipt strings, and emits `ApplicationPreLease`
only after validating the explicit lease identity and restore window. The
adapter is a testable interface; it does not contact a host or claim that
synthetic source objects are authenticated.

Evidence:

- Focused candidate tests: 4 passed.
- Complete `scripts/local-ai` suite: 216 passed, 4 expected macOS
  root-custody skips.
- No live entrypoint wiring or effect authorization was added.

Remaining gates are fixed root-owned Proxmox/TrueNAS/LXC adapters, source
authentication and custody, same-cycle backup/mirror evidence, measured
recovery/lag budget, target-Linux proof, rollback, and separate host-change
and application-only drill approvals.
