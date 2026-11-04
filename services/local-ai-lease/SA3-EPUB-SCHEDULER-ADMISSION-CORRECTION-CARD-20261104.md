# SA3 EPUB scheduler admission correction card — 2026-11-04

## Trigger and diagnosis

Booking `aster-stream-a-sa3-envelope-20261104-1230` was claimed exactly at
12:30 and failed before drain or model work. The retained owner traceback names
`EPUB narration timer and worker are not healthy`. The installed predicate
still requires the removed guest `epub-narration-worker.timer`, or a worker
that is active/activating.

Production has since graduated to a host-owned bounded scheduler. The observed
healthy state is:

- host `epub-narration-scheduler.timer`: enabled, active/waiting;
- guest `epub-narration-monitor.timer`: enabled, active/waiting;
- guest `epub-narration-worker.service`: inactive between bounded sessions,
  last result success and exit zero;
- scheduler and monitor each expose a future next trigger;
- the run retained no candidate result, drain state, lease/operation lock or
  candidate process; the lease is ready and production services are healthy.

The booked runner's postcheck reused the stale predicate, so its terminal state
reports `PRODUCTION_RESTORATION_INVALID` even though no drain occurred and
independent production checks pass. This is a diagnostic false negative, not a
production outage.

## Exact correction

Replace only the EPUB predicate in `full_inference_lab_sources.py`. Require the
host scheduler and guest monitor timers to be active and enabled. Accept the
worker only when its state is `inactive`, `active` or `activating` and its last
result is `success`. A failed worker or missing/disabled scheduler/monitor still
fails closed.

Update only the corresponding release-manifest pin and release name. The exact
source identities are:

- corrected source:
  `c07c2966a13144b8ca2b68639917381bad7381f9d8fa61adc265f1b30f59c5d9`;
- corrected release manifest:
  `d92f9b34c500310fd3427955a0dc53b5965400067edde36639312d1cc14266d0`.

The first inactive-install attempt failed closed during live admission
validation because a combined `systemctl show --property=ActiveState,Result`
query returned the two values in a different order than the source assumed.
Rollback restored both predecessor files and independent hash checks confirmed
the old installed baseline remained intact. Revision 2 queries each property
separately, so systemd property ordering is no longer part of the contract; it
also uses a fresh checkpoint and leaves the first retained checkpoint
untouched.

The new inactive installer requires the exact currently installed source and
manifest hashes, a ready lease and no drain/shared-operation state. It creates
a fresh root-only checkpoint, replaces exactly those two files, imports the
source, validates the live scheduler predicate and reloads the complete release
manifest. Any failure restores both old files. It starts no service, performs
no booking, model request, workload, restart or route change.

## Verification and next gate

The source/predicate, validator, runner, supersession, manifest and new-installer
revision-2 subset passes 33/33 tests. The wider historical suite remains intentionally
pin-sensitive and contains unrelated superseded-card failures; it is not used
to weaken this exact correction. After inactive installation, independently verify both installed
hashes, live predicate acceptance, complete manifest validation, ready lease,
absent shared state/locks and unchanged production services. The spent 12:30
booking may never be retried. A later fresh booking requires a new ledger-clear
window and the normal atomic runtime gates.
