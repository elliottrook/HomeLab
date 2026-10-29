# Aster Lab Hours reservation RC1 — qualification result

> Date: 2026-10-29 America/Vancouver
>
> Source: `336df57de7929dd0a3e612494ff769d3cb0ba225`
>
> Decision: **qualified**

## Installed boundary

The reservation ledger, dispatcher, fixed runner and Doctor were installed on
Proxmox under root custody. The dispatcher and Doctor timers are active. An
empty ledger causes no production effect. The installation changed no model,
backend, credential, firewall, backup schedule or host/guest boot state.

The authoritative ledger is `/var/lib/local-ai-lab/reservations`. Reservations
are bounded to 90 minutes with a 15-minute restoration buffer, accept only
registered workload names and are claimed atomically before any effect. The
shared operation lock and whole-host lease enforce exclusivity at runtime;
Doctor reports unsupported or unowned state.

Target-Linux staging, imports, systemd verification and the complete 123-test
Lab Hours suite passed. Three root-custody tests remained intentionally skipped
outside their root fixture.

## LH4 scheduled-pass evidence

The invalid-overlap and arbitrary-workload probes were rejected before any
effect. Two distinct scheduled reservations then completed:

- `lh4-pass-one-20261029`, 08:52:00–08:55:45 PDT: terminal `complete`, three
  requests, production restored.
- `lh4-pass-two-b-20261029`, 09:11:00–09:14:37 PDT: terminal `complete`, three
  requests, production restored.

After each pass the lease was ready, Doctor was healthy and no owner, guardian,
lab listener/process, drain state or lock remained.

## LH5 owner-loss evidence

The first controlled exercise, `lh5-owner-loss-c-20261029`, deliberately
removed the exact owner scope after durable state appeared. Production services
returned, but the guardian retained the drain state and lock until its fixed
deadline. Its terminal result was `no_go` at 09:55:01 PDT with phase
`guardian-recovery-postcheck` and code `SHARED_STATE_OR_LOCK_PRESENT`; Doctor
reported `UNOWNED_DRAIN_STATE` and the lease was ready.

The retained evidence exposed two deterministic recovery defects. The guardian
allowed only 120 seconds for the complete rescue validation, and a retry treated
the already restored accepted production GPU holder as continuing lab
occupancy. Source now allows a 300-second rescue and accepts only the exact
pinned production holder during recovery while still rejecting an unknown
holder or any remaining lab scope, listener or process. The focused 26-test
recovery suite and the complete 123-test Lab Hours suite passed locally and in
target-Linux staging.

The corrected runtime, guardian and manifest were installed with the former
files preserved at
`/root/aster-lab-hours-recovery-fix-rollback-20261029-0956`. Their installed
SHA-256 values are:

- runtime: `5fa48df16c4db8d2eedcd4a8ab9d615cc07519b713a0028c20019d84ae06ac3d`
- guardian: `688d995dafd33b7b905fb7351bf365a0d0fdcc20766e5c497551d2cc0846cc35`
- manifest: `e4e9e4bf5d9456c0b2e74d479866510b48d532e165569ce7c52c07ff9ac6f447`

The exact retained owner/lease/generation rescue completed with
`rescue-restored`. The drain state and lock cleared, the lease returned ready,
all three guests remained running, Proxmox daemons were active and Doctor
returned healthy with no codes. The failed reservation's 15-minute restoration
buffer was honored before scheduling a fresh owner-loss exercise.

The fresh booking `lh5-owner-loss-d-20261029` was claimed exactly at 10:11:00
PDT. The fixed owner-loss workload removed its exact owner, the independent
guardian restored production, and the booking reached terminal `complete` at
10:16:13 PDT (313 seconds). The terminal record contains
`production_restored=true`, `request_count=0` and the fixed owner-loss workload
identity.

Independent postchecks found the state and lock absent, no runner, guardian,
lab listener or lab process, lease `ready`, LXC 104/110/116 running, Proxmox
daemons active, Aster Agent, accepted llama.cpp/SYCL and Speech active, News
timers active/enabled, the EPUB timer active/enabled and its resumable worker
activating. The production authentication probe exited zero. Doctor returned
`healthy`, no codes, zero active reservations and the new completion epoch.

## Operating decision

LH4 and LH5 are complete. The reservation-driven service is the graduated
operating boundary for exclusive Lab Hours. All supported schedulers must check
the ledger before proposing or scheduling exclusive work; the host still
enforces an atomic claim, shared lock and whole-host lease before effects.
Doctor detects missed bookings and unsupported bypass state. Root can always
bypass a host-local policy, so retained audit evidence and Doctor detection are
the enforcement boundary for unregistered administrative actions.

All failed and successful booking records and attempt evidence are retained.
