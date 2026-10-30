# M3 mount canonicalization correction — 2026-10-30

Status: **SOURCE CORRECTED; SPENT BOOKING NOT RETRIED**

Booking `aster-stream-a-m3-35b-20261030-0500` claimed once and ended
`NO_GO` before any 35B process or public-case request. The owner first raised
`M3_CANDIDATE_MOUNT_INVALID`; recovery then retained state with
`LXC110 mount state is foreign or uncertain`. The booked terminal projection
therefore reports `SHARED_STATE_OR_LOCK_PRESENT`, phase `owner-transaction`
and `production_restored=false`.

The residual `mp0` was the transaction-owned mount with the exact source,
guest path and values, but Proxmox serialized its options as
`backup=0,ro=1`. The observer required the source spelling
`ro=1,backup=0`, so it rejected the mount just created by `pct set` and then
prevented automatic recovery from removing it. This was a deterministic
order-sensitive comparison defect, not a foreign mount.

The observer now parses the single fixed `mp0` into its source plus an exact
key/value map. It accepts only the same source and the exact `mp`, `ro` and
`backup` values in any serialization order; duplicate, malformed, additional
or changed options remain foreign and fail closed. The registration and
release manifest are repinned to:

- `full_aster_first_screen_observer.py`:
  `e30ed0e5faa2949f7734e4b61488092d8c0d178484db689b8b684eeac5449cff`
- `lab_hours_workloads.py`:
  `ca25a6378b4dcd7501dbe4146544cd8813a08c64ae037302f9251c88a3793ddd`
- `lab_hours_release_manifest.json`:
  `7813b11746144e2cafaf0502f71be4ef89002b4fe77f5c070d9599bc67454a22`

The Lab Hours discovery suite passes 31/31. The focused observer, recovery,
M3 transaction, M3 guardian and runtime suite passes 27/27, including the
actual reordered Proxmox spelling and rejection of extra options. Synthetic
joined success still returns 24 requests, 23 exact, zero safety failures and
`production_restored=true`.

The spent booking is retained and must not be retried or rewritten. This
correction does not schedule another booking, promote the 35B model, open a
private calibration or holdout, or enable automatic routing.
