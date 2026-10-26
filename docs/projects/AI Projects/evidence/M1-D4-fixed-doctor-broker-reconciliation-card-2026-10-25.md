# M1/D4 fixed Doctor broker reconciliation — replacement and restart card

**Date:** 2026-10-25
**Status:** corrected retry candidate; first attempt rolled back; new exact approval required
**Manifest:** `scripts/deploy/fixed-doctor-broker-reconciliation-manifest.json`

## Why the earlier candidate is superseded

The deployed LXC104 broker has newer Forgejo project-document support that was
not present in the earlier fixed Doctor candidate. Replacing the live sources
with that earlier candidate would remove the
`forgejo.write.project-documents` registration, its dedicated socket and the
`create_file_batch` route. That candidate is therefore rejected for live use.

This reconciliation starts from the exact deployed predecessors, requires
their SHA-256 hashes, preserves the newer Forgejo route byte-for-byte in
behavior, and adds only the fixed Doctor administration and transport path.
The generator refuses source drift.

## Exact candidate

Replace exactly two files in LXC104:

| File | Required predecessor | Candidate | Mode |
|---|---|---|---|
| `/opt/homelab-broker/broker_admin.py` | `00216b27e179d936e1b5fd9feb1ca17dc25bb6af3e34b044408ae21133924e8b` | `e90acd24acfa13f959070f2c791d29ea28ebf1d4240edd5a9b39b54dfc7ef4aa` | root:root `0700` |
| `/opt/homelab-broker/broker_service.py` | `05a555241b97ad7e6a9d268ad91426af0432fb0ae0785dabf46bf4081e713ccb` | `c6217f4988510b4d38581829b4f6b333487b1cd35732a6ba5b3d82dcc69b627e` | root:root `0644` |

`broker_core.py` must remain at
`2fdb80964984fed5cf539f12a62d0058ba9eb9088861425858109fabc7dabf99`.
The systemd unit is unchanged. Its existing command does not pass the new
fixed-Doctor socket flag, so the reviewed default
`/run/aster-fixed-doctor/gateway.sock` applies while all existing explicit
Forgejo and lab-operation sockets remain unchanged.

## First attempt correction

The first approved attempt rolled back after its postcheck used Unix user
`aster`, which does not have broker-socket access. Recovery initially exposed a
second script defect: the SQLite backup was restored as root:root. Production
was recovered by restoring its measured `hlabroker:hlabroker` mode `0600`
custody and restarting only the broker. The complete bounded record is in
[the rollback result](M1-D4-fixed-doctor-broker-first-attempt-rollback-2026-10-25.md).

The corrected apply script is SHA-256
`d69a6c42bfc13b9f66f568077e5856783a4bf0f337264f1d877434be9408c28f`.
It preflights and postchecks health as registered client `hlabagent`, verifies
database and socket custody before replacement, and restores SQLite as
`hlabroker:hlabroker` mode `0600` during rollback.

## Bounded live procedure

1. Recheck both predecessor hashes, ownership/modes, `broker_core.py`, the
   service unit, active broker state and zero fixed-Doctor database rows.
2. Preserve the two sources and a consistent root-only SQLite backup in one
   dated checkpoint. Record its hashes without reading request payloads.
3. Stage both candidates on LXC104, verify hashes, modes and Python 3.13
   imports/compilation before touching live paths.
4. Atomically replace the two files, preserving the recorded ownership/modes.
5. Restart only `homelab-broker.service` once.
6. Require active/running state, no restart loop, the registered Aster user's
   ordinary broker health response, unchanged project-document capability and
   routing metadata, and zero fixed-Doctor agents/services/capabilities/grants/
   requests. Aster Agent must remain healthy.
7. Verify both fixed Doctor services remain disabled/inactive and both fixed
   sockets remain absent.

## Rollback

On any staging, replacement, import, restart or postcheck failure, restore both
exact predecessor sources and the consistent database checkpoint, restart only
`homelab-broker.service`, and re-run the same broker/Aster and zero-row checks.
Do not continue to enrollment or activation after a rollback.

## Evidence already complete

- the generator reproduced both candidates from captured exact live sources;
- the two generated files match the committed candidates byte-for-byte;
- local Python compilation passed;
- 51 focused broker/fixed-Doctor tests and the complete 125-test credential-broker suite passed, including new regression tests
  for `enable-forgejo-project-documents`, `create_file_batch`, the dedicated
  project-write socket, empty-only fixed requests and the fixed gateway route;
- the target currently reports the required predecessor hashes, root ownership,
  modes `0700`/`0644`, active broker with zero restarts, Python 3.13.5 and the
  expected explicit project-document socket in `ExecStart`.

Target-Linux staging/import checks and the live restart are intentionally held
inside the single replacement gate so the staged bytes cannot drift from the
approved candidate.

## Exclusions

No fixed-Doctor enrollment or grant, caller/gateway activation, fixed read,
model call, Forgejo write, project-document change, Companion change, schedule
change, F2/F6/B60 action, credential change, database payload inspection or Git
push is included.
