# Common host-exclusion install preflight — mismatch

**Observed:** 2026-10-16, America/Vancouver. Read-only SSH preflight only;
no files, timers, leases, services or schedules were changed.

The proposed disabled-install card cannot be executed as written. Proxmox
reported these installed paths:

- `lease_controller_candidate.py` present at the expected reviewed hash
  `e5d328937ea482de4b365e0be1869cabd3cd589eae86a2240b1d72bd5ae47226`.
- `retained_archive_producer_candidate.py` present at the earlier disabled
  hash `f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b`.
- `full_stop_acquire_candidate.py` present, but hash
  `bb0e1a2cc1efa2c904d374a9fc4c5cac5891bf69d63b689e2c130fa84ccd9e3b`
  does not match the proposed card.
- `host_exclusion.py`, `retained_archive_timing_observer.py`, and
  `application_b60_controller.py` are absent.

The whole-host and application-B60 lease state/lock paths were absent. The
watchdog, owner-heartbeat and application watchdog timers were disabled and
inactive; the A1 test unit was absent. Host load was approximately
`0.61, 0.78, 0.88`.

**Decision:** failed preflight. Do not install or replace files until the
source pins and add/replace boundaries are reconciled against the actual
installed tree. This does not advance F2/F3/F6 and does not authorize a live
drill.
