# Lab Hours reservation and recovery qualification — 2026-10-29

## Decision

**LH4 and LH5 are complete.** The reservation-driven Lab Hours service is the
graduated operating boundary for exclusive B60 work.

## Installed contract

Proxmox owns a root-only reservation ledger, one-minute dispatcher and
five-minute Doctor. Reservations accept only registered fixed workloads, last
at most 90 minutes, include a 15-minute restoration buffer and are claimed
atomically before any effect. The runner also requires the shared operation
lock and whole-host lease. An empty ledger produces no effect.

The target-Linux staging checks, imports, systemd verification and complete
123-test Lab Hours suite passed. Invalid overlap and arbitrary-workload probes
were rejected before effects.

## LH4 evidence

- `lh4-pass-one-20261029`: 08:52:00–08:55:45 PDT, terminal `complete`, three
  requests, production restored.
- `lh4-pass-two-b-20261029`: 09:11:00–09:14:37 PDT, terminal `complete`, three
  requests, production restored.

Both left the lease ready, Doctor healthy and no owner, guardian, lab
listener/process, state or lock.

## LH5 evidence and correction

The first owner-loss attempt deliberately removed its owner after durable
state appeared. It restored production but retained state and lock, ending
`no_go` at 09:55:01 PDT with
`guardian-recovery-postcheck/SHARED_STATE_OR_LOCK_PRESENT`. Doctor reported
`UNOWNED_DRAIN_STATE`.

The retained evidence identified two deterministic defects: a 120-second
rescue budget was too short for full validation, and recovery retries rejected
the exact accepted production GPU holder after production had restarted. The
correction grants 300 seconds and accepts only that exact pinned production
holder during recovery while still rejecting unknown holders and every lab
scope, listener or process. The focused 26-test recovery suite and complete
123-test suite passed locally and in target-Linux staging.

Installed corrected hashes:

- runtime `5fa48df16c4db8d2eedcd4a8ab9d615cc07519b713a0028c20019d84ae06ac3d`
- guardian `688d995dafd33b7b905fb7351bf365a0d0fdcc20766e5c497551d2cc0846cc35`
- manifest `e4e9e4bf5d9456c0b2e74d479866510b48d532e165569ce7c52c07ff9ac6f447`

The exact retained-state rescue then returned `rescue-restored`, cleared state
and lock and made Doctor healthy. After the failed booking's 15-minute buffer,
`lh5-owner-loss-d-20261029` was claimed exactly at 10:11:00 PDT and completed
at 10:16:13 PDT (313 seconds). Its terminal record contains
`production_restored=true`, `request_count=0` and the registered owner-loss
workload.

Independent postchecks found no owner, guardian, runner, lab listener/process,
state or lock; lease `ready`; LXC 104/110/116 running; Proxmox daemons active;
Aster Agent, accepted llama.cpp/SYCL and Speech active; News timers and EPUB
timer active/enabled; EPUB worker resuming; production authentication exit
zero; and Doctor healthy with no codes and zero active reservations.

No model, backend, credential, firewall, backup schedule or boot state changed.
All booking and attempt evidence is retained.
