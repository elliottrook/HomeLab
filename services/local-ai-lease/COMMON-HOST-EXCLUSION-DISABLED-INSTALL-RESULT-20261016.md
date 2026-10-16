# Common host exclusion — failed disabled install and verified rollback

**Observed:** October 16, 2026, America/Vancouver. Jason approved the exact
six-file, three-add/three-replace disabled installation described by the first
card. No timer, lease, archive scan, receipt, service stop, model call or
schedule change was authorized.

Fresh read-only preflight matched all three pinned replacement hashes and all
three add-only absences. `/var/lib/local-ai-lab` was root-owned mode 0700;
whole-host and application lease state/locks were absent; relevant timers were
disabled/inactive; backup process count was zero. LXC104/110/116 production
services were active.

The first transfer archive contained macOS AppleDouble entries. The bounded
installer rejected its unexpected members **before modifying installed files**.
The archive was rebuilt with `COPYFILE_DISABLE=1`, and the six source hashes
matched the reviewed card. A root-only checkpoint of the three originals was
created at `/var/lib/local-ai-lab/host-exclusion-checkpoint.8t9f7gwn` before
the six files were staged.

Target-Linux import validation then failed: the staged
`application_b60_controller.py` could not import `application_b60_lease` from
`/usr/local/libexec/local-ai-lease`. Read-only inspection established that the
application controller and its dependency actually live in
`/usr/local/libexec/aster-a1`, at installed hashes
`3daa4204b1e9515e397680dc51bb2ed96994d2a273e0c2c3ef87f728ce6a41af`
and `deaf278c8bc3234f3150f1c3ee696b3cc0cdb55e97c575fec6efb65d6ef9c95d`.
The existing application controller imports successfully from that directory.
The earlier card's single-directory deployment assumption was false.

The approved rollback was executed while both lease namespaces remained
absent. The three originals returned to their preflight hashes:

| Whole-host candidate | Restored SHA-256 |
|---|---|
| `retained_archive_producer_candidate.py` | `f3ae1a83f16e5b9c1bca571826029603e4c8d88fc6b529bfe79ffcd465288a3b` |
| `lease_controller_candidate.py` | `e5d328937ea482de4b365e0be1869cabd3cd589eae86a2240b1d72bd5ae47226` |
| `full_stop_acquire_candidate.py` | `bb0e1a2cc1efa2c904d374a9fc4c5cac5891bf69d63b689e2c130fa84ccd9e3b` |

The three added paths are absent again. The old manual controller, recovery
executor and retained integrity module hashes match the preflight; the Proxmox
backup schedule digest remained
`ba63cd4f34e305fef29952f388799a0b0641806644105dde43a33fb73b36f622`.
LXC104/110/116 services are active, watchdog/heartbeat timers remain
disabled/inactive, and no lease state/lock exists. The root-only source staging
directory and checkpoint were retained for provenance, not enabled.

**Decision:** first card failed target-Linux validation and is superseded. No
F2/F3/F6 gate advanced. Any corrected installation must pin both module roots,
the existing application-controller byte hash and a new rollback scope, then
receive a new exact host-change approval before execution.
